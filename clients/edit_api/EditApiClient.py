from typing import Callable
from urllib import request
import json

from qgis._core import QgsMessageLog, Qgis

from ...settings import MESSAGE_CATEGORY
from .EditApiClientSettings import EditApiClientSettings
from .Models.BranchModel import BranchModel
from .Models.SnapshotCommitModel import SnapshotCommitModel

class EditApiClient(object):
    def __init__(self, settings: EditApiClientSettings):
        self.settings = settings

    def get_latest_commit_for_snapshot_with_name(self, snapshot_name: str, callback: Callable[[SnapshotCommitModel], None]):
        if callback is None:
            raise Exception("No callback given for fetch_non_blocking")

        url = f"{self.settings.url}snapshot/{snapshot_name}/commit/latest"
        QgsMessageLog.logMessage(f"{EditApiClient.__name__} GET {url}", MESSAGE_CATEGORY, Qgis.Info)

        try:
            response = request.urlopen(request.Request(url))
            json_string = response.read().decode("utf-8")
            QgsMessageLog.logMessage(f"{EditApiClient.__name__} GET response {json_string}", MESSAGE_CATEGORY, Qgis.Info)
            json_object = json.loads(json_string)
            QgsMessageLog.logMessage(f"{EditApiClient.__name__} GET response {json_object['id']}", MESSAGE_CATEGORY, Qgis.Info)
            callback(SnapshotCommitModel.from_json(json_object))
        except Exception as e:
            raise e

    def get_branch(self, branch_id: str, callback: Callable[[BranchModel], None]):
        if callback is None:
            raise Exception("No callback given for fetch_non_blocking")

        url = f"{self.settings.url}branch/{branch_id}"
        QgsMessageLog.logMessage(f"{EditApiClient.__name__} GET {url}", MESSAGE_CATEGORY, Qgis.Info)

        try:
            response = request.urlopen(request.Request(url))

            callback(BranchModel.from_json(json.loads(response.read().decode("utf-8"))))
        except Exception as e:
            raise e