from typing import Callable
from urllib import request
import json

from .EditApiClientSettings import EditApiClientSettings
from .Models.BranchModel import BranchModel

class EditApiClient(object):
    def __init__(self, settings: EditApiClientSettings, get_token=None):
        self.settings = settings
        self._get_token = get_token

    def _build_request(self, url: str) -> request.Request:
        req = request.Request(url)
        if self._get_token is not None:
            token = self._get_token()
            if token:
                req.add_header("Authorization", f"Bearer {token}")
        return req

    def get_branch(self, branch_id: str, callback: Callable[[BranchModel], None]):
        if callback is None:
            raise Exception("No callback given")

        url = f"{self.settings.url}branch/{branch_id}"

        try:
            response = request.urlopen(self._build_request(url), timeout=self.settings.timeout)
            json_string = response.read().decode("utf-8")
            json_object = json.loads(json_string)
            callback(BranchModel.from_json(json_object))
        except Exception as e:
            raise e
