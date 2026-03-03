from typing import Callable, Optional
from urllib import request
import json

from .ApiClientSettings import ApiClientSettings
from .Models.ProjectModel import ProjectModel
from .Models.ResponseModel import ResponseModel

class ApiClient(object):
    def __init__(self, settings: ApiClientSettings, get_token: Callable[[], Optional[str]] = None):
        self.settings = settings
        self._get_token = get_token

    def _build_request(self, url: str, data: bytes = None, extra_headers: dict = None) -> request.Request:
        req = request.Request(url, data=data)
        if extra_headers:
            for key, value in extra_headers.items():
                req.add_header(key, value)
        if self._get_token is not None:
            token = self._get_token()
            if token:
                req.add_header("Authorization", f"Bearer {token}")
        return req

    def get_project(self, project_id: str, callback: Callable[[ResponseModel[ProjectModel]], None]):
        if callback is None:
            raise Exception("No callback given for fetch_non_blocking")

        url = f"{self.settings.url}v2.0/plugin/project/{project_id}/"

        try:
            response = request.urlopen(self._build_request(url), timeout=self.settings.timeout)
            json_string = response.read().decode("utf-8")
            json_object = json.loads(json_string)
            callback(ProjectModel.from_response_json(json_object))
        except Exception as e:
            raise e

    def get_projects(self, callback: Callable[[list], None]):
        if callback is None:
            raise Exception("No callback given")

        url = f"{self.settings.url}v2.0/project/"

        try:
            req = self._build_request(url)
            response = request.urlopen(req, timeout=self.settings.timeout)
            json_string = response.read().decode("utf-8")
            data = json.loads(json_string)
            projects = data.get("details", []) if isinstance(data, dict) else data
            # build org name lookup from included organizations
            org_lookup = {}
            if isinstance(data, dict):
                for org in data.get("organizations", []):
                    org_lookup[org.get("id", "")] = org.get("name", "")
            # attach org name to each project
            for project in projects:
                org_id = project.get("organization", "")
                project["_organization_name"] = org_lookup.get(org_id, "")
            callback(projects)
        except Exception as e:
            raise e
