from typing import Callable, Optional
from urllib import request
import json
import uuid

from qgis._core import QgsMessageLog, Qgis
from ...settings import MESSAGE_CATEGORY
from .ApiClientSettings import ApiClientSettings
from .Models.DatasetModel import DatasetLocationModel, DatasetModel, DatasetTripModel
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
                {"type": "scenario", "children": [], "parents": []},
                {"type": "dataset", "children": [], "parents": []}
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

    def get_dataset(self, dataset_id: str, callback: Callable):
        if callback is None:
            raise Exception("No callback given")

        url = f"{self.settings.url}v3.0/data/"
        body = json.dumps({
            "type": "dataset",
            "id": dataset_id,
            "children": [
                {"type": "dataset_trip", "children": [], "parents": []},
                {"type": "dataset_location", "children": [], "parents": []}
            ],
            "parents": []
        }).encode("utf-8")

        try:
            req = self._build_request(url, data=body, extra_headers={"Content-Type": "application/json"})
            response = request.urlopen(req, timeout=self.settings.timeout)
            json_string = response.read().decode("utf-8")
            data = json.loads(json_string)

            trips = []
            locations = {}
            for item in data:
                item_type = item.get("_type", "")
                if item_type == "dataset_trip":
                    trips.append(DatasetTripModel.from_json(item))
                elif item_type == "dataset_location":
                    loc = DatasetLocationModel.from_json(item)
                    locations[loc.global_id] = loc
            callback(trips, locations)
        except Exception as e:
            QgsMessageLog.logMessage(f"get_dataset: ERROR {e}", MESSAGE_CATEGORY, Qgis.Warning)
            raise e

    def upload_dataset(self, project_id: str, name: str, description: str,
                       locations: list, trips: list, callback: Callable):
        if callback is None:
            raise Exception("No callback given")

        url = f"{self.settings.url}v3.0/data/"

        dataset_id = str(uuid.uuid4())

        data_objects = []

        # Dataset object
        data_objects.append({
            "_type": "dataset",
            "id": dataset_id,
            "changeType": "new",
            "name": name,
            "description": description,
            "project": project_id
        })

        # Location objects (must come before trips)
        for loc in locations:
            data_objects.append({
                "_type": "dataset_location",
                "id": loc["id"],
                "changeType": "new",
                "longitude": loc["longitude"],
                "latitude": loc["latitude"],
                "dataset": dataset_id
            })

        # Trip objects
        for trip in trips:
            data_objects.append({
                "_type": "dataset_trip",
                "id": str(uuid.uuid4()),
                "changeType": "new",
                "origin": trip["origin"],
                "destination": trip["destination"],
                "count": trip["count"],
                "profile": trip["profile"],
                "dataset": dataset_id
            })

        body = json.dumps(data_objects).encode("utf-8")

        try:
            QgsMessageLog.logMessage(
                f"upload_dataset: PUT {url} ({len(data_objects)} objects)",
                MESSAGE_CATEGORY, Qgis.Info)
            req = self._build_request(url, data=body, extra_headers={"Content-Type": "application/json"})
            req.method = "PUT"
            response = request.urlopen(req, timeout=60)
            QgsMessageLog.logMessage("upload_dataset: success", MESSAGE_CATEGORY, Qgis.Info)
            callback()
        except Exception as e:
            QgsMessageLog.logMessage(f"upload_dataset: ERROR {e}", MESSAGE_CATEGORY, Qgis.Warning)
            raise e

    def get_projects(self, callback: Callable[[list], None]):
        if callback is None:
            raise Exception("No callback given")

        url = f"{self.settings.url}v3.0/data/"
        body = json.dumps({
            "type": "project",
            "children": [],
            "parents": [{"type": "organization", "children": [], "parents": []}]
        }).encode("utf-8")

        try:
            QgsMessageLog.logMessage(f"get_projects: POST {url}", MESSAGE_CATEGORY, Qgis.Info)
            req = self._build_request(url, data=body, extra_headers={"Content-Type": "application/json"})
            response = request.urlopen(req, timeout=self.settings.timeout)
            json_string = response.read().decode("utf-8")
            QgsMessageLog.logMessage(f"get_projects: response {json_string[:500]}", MESSAGE_CATEGORY, Qgis.Info)
            data = json.loads(json_string)

            # v3 returns flat array of DataObjects, separate by _type
            org_lookup = {}
            projects = []
            for item in data:
                if item.get("_type") == "organization":
                    org_lookup[item.get("id", "")] = item.get("name", "")
                elif item.get("_type") == "project":
                    projects.append(item)

            QgsMessageLog.logMessage(f"get_projects: found {len(projects)} projects, {len(org_lookup)} orgs", MESSAGE_CATEGORY, Qgis.Info)
            # attach org name to each project
            for project in projects:
                org_id = project.get("organization", "")
                project["_organization_name"] = org_lookup.get(org_id, "")
            callback(projects)
        except Exception as e:
            QgsMessageLog.logMessage(f"get_projects: ERROR {e}", MESSAGE_CATEGORY, Qgis.Warning)
            raise e
