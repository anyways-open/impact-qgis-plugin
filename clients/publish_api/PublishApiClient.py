from typing import Callable
from urllib import request
import json

from qgis._core import QgsMessageLog, Qgis

from .Models.RouteMatrixResponse import RouteMatrixResponse
from ...settings import MESSAGE_CATEGORY
from . import PublishApiClientSettings
from .Models.RouteMatrixRequest import RouteMatrixRequest

class PublishApiClient(object):
    def __init__(self, settings: PublishApiClientSettings):
        self.settings = settings

    def post_branch_many_to_many(self, commit_id, route_matrix_request: RouteMatrixRequest, callback: Callable[[RouteMatrixResponse], None]):
        if callback is None:
            raise Exception("No callback given for fetch_non_blocking")

        headers = {"Content-Type": "application/json"}

        url = f"{self.settings.url}branch/commit/{commit_id}/routing/many-to-many"

        try:
            data = route_matrix_request.to_json().encode('UTF-8')
            response = request.urlopen(request.Request(url, data=data,
                                      headers=headers))
            json_response = json.loads(response.read().decode("UTF-8"))
            callback(RouteMatrixResponse.from_json(json_response))
        except Exception as e:
            raise e

    def post_snapshot_many_to_many(self, commit_id, route_matrix_request: RouteMatrixRequest, callback: Callable[[RouteMatrixResponse], None]):
        if callback is None:
            raise Exception("No callback given for fetch_non_blocking")

        headers = {"Content-Type": "application/json"}

        url = f"{self.settings.url}snapshot/commit/{commit_id}/routing/many-to-many"

        try:
            data = route_matrix_request.to_json().encode('UTF-8')
            response = request.urlopen(request.Request(url, data=data,
                                      headers=headers))
            json_response = json.loads(response.read().decode("UTF-8"))
            callback(RouteMatrixResponse.from_json(json_response))
        except Exception as e:
            raise e
