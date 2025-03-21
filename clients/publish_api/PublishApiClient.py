from typing import Callable
from urllib import request
import json
from urllib.error import URLError
from socket import timeout

from qgis._core import QgsMessageLog, Qgis

from .Models.Compact.MatrixCompactResponse import MatrixCompactResponse
from ...Result import Result
from .Models.RouteMatrixResponse import RouteMatrixResponse
from ...settings import MESSAGE_CATEGORY
from . import PublishApiClientSettings
from .Models.RouteMatrixRequest import RouteMatrixRequest

class PublishApiClient(object):
    def __init__(self, settings: PublishApiClientSettings):
        self.settings = settings

    def post_branch_many_to_many(self, commit_id, route_matrix_request: RouteMatrixRequest, callback: Callable[[Result[RouteMatrixResponse]], None]):
        if callback is None:
            raise Exception("No callback given")

        def handle_result(response_result: Result[bytes]) -> None:
            if response_result.result is None:
                callback(Result(message=response_result.message))

            callback(Result(RouteMatrixResponse.from_json(json.loads(response_result.result))))

        self.fetch(f"{self.settings.url}branch/commit/{commit_id}/routing/many-to-many",
                   route_matrix_request.to_json().encode('UTF-8'),
                   {"Content-Type": "application/json"}, handle_result)

    def post_snapshot_many_to_many(self, commit_id, route_matrix_request: RouteMatrixRequest, callback: Callable[[Result[RouteMatrixResponse]], None]):
        if callback is None:
            raise Exception("No callback given for fetch_non_blocking")

        def handle_result(response_result: Result[bytes]) -> None:
            if response_result.result is None:
                callback(Result(message=response_result.message))

            callback(Result(RouteMatrixResponse.from_json(json.loads(response_result.result))))

        self.fetch(f"{self.settings.url}snapshot/commit/{commit_id}/routing/many-to-many",
                   route_matrix_request.to_json().encode('UTF-8'),
                   {"Content-Type": "application/json"}, handle_result)

    def post_branch_many_to_many_compact(self, commit_id, route_matrix_request: RouteMatrixRequest, callback: Callable[[Result[MatrixCompactResponse]], None]):
        if callback is None:
            raise Exception("No callback given")

        def handle_result(response_result: Result[bytes]) -> None:
            if response_result.result is None:
                callback(Result(message=response_result.message))

            callback(Result(MatrixCompactResponse.from_json(json.loads(response_result.result))))

        self.fetch(f"{self.settings.url}branch/commit/{commit_id}/routing/many-to-many/compact",
                   route_matrix_request.to_json().encode('UTF-8'),
                   {"Content-Type": "application/json"}, handle_result)

    def post_snapshot_many_to_many_compact(self, commit_id, route_matrix_request: RouteMatrixRequest, callback: Callable[[Result[MatrixCompactResponse]], None]):
        if callback is None:
            raise Exception("No callback given for fetch_non_blocking")

        def handle_result(response_result: Result[bytes]) -> None:
            if response_result.result is None:
                callback(Result(message=response_result.message))

            callback(Result(MatrixCompactResponse.from_json(json.loads(response_result.result))))

        self.fetch(f"{self.settings.url}snapshot/commit/{commit_id}/routing/many-to-many/compact",
                   route_matrix_request.to_json().encode('UTF-8'),
                   {"Content-Type": "application/json"}, handle_result)

    def fetch(self, url: str, data: bytes, headers: dict[str, str], callback: Callable[[Result[bytes]], None]) -> None:
        try:
            response = request.urlopen(request.Request(url, data=data,
                                      headers=headers), timeout=self.settings.timeout)
            raw_json = response.read().decode("UTF-8")
            # QgsMessageLog.logMessage(f"raw_json: {raw_json}", MESSAGE_CATEGORY, Qgis.Info)
            callback(Result(raw_json))
        except Exception as e:
            callback(Result(message=f"Request failed: {e}"))