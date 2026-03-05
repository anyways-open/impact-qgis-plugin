from typing import Callable
from urllib import request
import json

from qgis._core import QgsMessageLog, Qgis

from ...settings import MESSAGE_CATEGORY
from ...Result import Result
from .Models.AdHocRoutesResponse import AdHocRoutesResponse
from .PublishApiClientSettings import PublishApiClientSettings
from .Models.AdHocRoutesRequest import AdHocRoutesRequest

class PublishApiClient(object):
    def __init__(self, settings: PublishApiClientSettings, get_token=None):
        self.settings = settings
        self._get_token = get_token

    def post_ad_hoc_routes(self, commit_id: str, ad_hoc_request: AdHocRoutesRequest, callback: Callable[[Result[AdHocRoutesResponse]], None]):
        if callback is None:
            raise Exception("No callback given")

        url = f"{self.settings.url}v3.0/cachedroutes/{commit_id}"

        try:
            request_json = ad_hoc_request.to_json()
            raw_json = self._fetch(url, request_json.encode('UTF-8'), {"Content-Type": "application/json"})
            response_data = json.loads(raw_json)
            accumulated = AdHocRoutesResponse.from_json(response_data)

            # batch poll until complete
            while accumulated.batch is not None:
                batch_url = f"{self.settings.url}v3.0/cachedroutes/{commit_id}/batch/{accumulated.batch}"
                batch_raw = self._fetch(batch_url, None, {})
                batch_data = json.loads(batch_raw)
                batch_response = AdHocRoutesResponse.from_json(batch_data)
                accumulated = accumulated.merge(batch_response)

            callback(Result(accumulated))
        except Exception as e:
            callback(Result(message=f"Request failed: {e}"))

    def _fetch(self, url: str, data: bytes, headers: dict[str, str]) -> str:
        if self._get_token is not None:
            token = self._get_token()
            if token:
                headers["Authorization"] = f"Bearer {token}"
        response = request.urlopen(request.Request(url, data=data,
                                  headers=headers), timeout=self.settings.timeout)
        return response.read().decode("UTF-8")
