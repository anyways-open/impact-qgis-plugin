from typing import Callable
from urllib import request
import json

from .ApiClientSettings import ApiClientSettings
from .Models.ProjectModel import ProjectModel
from .Models.ResponseModel import ResponseModel

class ApiClient(object):
    def __init__(self, settings: ApiClientSettings):
        self.settings = settings

    def get_project(self, project_id: str, callback: Callable[[ResponseModel[ProjectModel]], None]):
        if callback is None:
            raise Exception("No callback given for fetch_non_blocking")

        url = f"{self.settings.url}v2.0/plugin/project/{project_id}/"

        try:
            response = request.urlopen(request.Request(url), timeout=self.settings.timeout)
            json_string = response.read().decode("utf-8")
            json_object = json.loads(json_string)
            callback(ProjectModel.from_response_json(json_object))
        except Exception as e:
            raise e
