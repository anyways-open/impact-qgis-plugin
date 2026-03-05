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

        url = f"{self.settings.url}v3.0/data/"
        body = json.dumps({
            "type": "project",
            "id": project_id,
            "children": [
                {"type": "network", "children": [], "parents": []},
                {"type": "scenario", "children": [], "parents": []}
            ],
            "parents": [
                {"type": "organization", "children": [], "parents": []}
            ]
        }).encode("utf-8")

        try:
            req = self._build_request(url, data=body, extra_headers={"Content-Type": "application/json"})
            response = request.urlopen(req, timeout=self.settings.timeout)
            json_string = response.read().decode("utf-8")
            data = json.loads(json_string)
            callback(ProjectModel.from_response_json(data))
        except Exception as e:
            raise e

    def get_projects(self, callback: Callable[[list], None]):
        if callback is None:
            raise Exception("No callback given")

        url = f"{self.settings.url}v3.0/data/"
        body = json.dumps({
            "type": "organization",
            "children": [{"type": "project", "children": [], "parents": []}],
            "parents": []
        }).encode("utf-8")

        try:
            req = self._build_request(url, data=body, extra_headers={"Content-Type": "application/json"})
            response = request.urlopen(req, timeout=self.settings.timeout)
            json_string = response.read().decode("utf-8")
            data = json.loads(json_string)

            # v3 returns flat array of DataObjects, separate by _type
            org_lookup = {}
            projects = []
            for item in data:
                if item.get("_type") == "organization":
                    org_lookup[item.get("id", "")] = item.get("name", "")
                elif item.get("_type") == "project":
                    projects.append(item)

            # attach org name to each project
            for project in projects:
                org_id = project.get("organization", "")
                project["_organization_name"] = org_lookup.get(org_id, "")
            callback(projects)
        except Exception as e:
            raise e
