from typing import Optional

from qgis.core import (
    QgsTask, QgsMessageLog, Qgis
)

from .RouteResult import RouteResult
from ...clients.publish_api.Models.RouteResponse import RouteResponse
from ...clients.publish_api.Models.RouteMatrixResponse import RouteMatrixResponse
from ...Result import Result
from ...clients.publish_api.PublishApiClient import PublishApiClient
from ...clients.edit_api.EditApiClient import EditApiClient
from ...clients.edit_api.EditApiClientSettings import EditApiClientSettings
from ...clients.edit_api.Models.BranchModel import BranchModel
from ...clients.edit_api.Models.SnapshotCommitModel import SnapshotCommitModel
from ...clients.publish_api.Models.RouteMatrixRequest import RouteMatrixRequest
from ...clients.publish_api.PublishApiClientSettings import PublishApiClientSettings
from ...settings import MESSAGE_CATEGORY
from .RoutingTaskSettings import RoutingTaskSettings, NetworkCommit

class RoutingTask(QgsTask):
    def __init__(self, settings: RoutingTaskSettings) -> None:
        super().__init__(f"Routing for layer {settings.name}", QgsTask.CanCancel)
        self.settings = settings
        self.data = list[RouteResult]()
        self.exception: Optional[Exception] = None

    def run(self):
        QgsMessageLog.logMessage(f"{self.description()} started!", MESSAGE_CATEGORY, Qgis.Info)

        self.setProgress(0)

        try:
            def plan_with_network(network: NetworkCommit):
                public_api = PublishApiClient(PublishApiClientSettings())

                i: int = 0
                while i < len(self.settings.matrix.elements):
                    if self.isCanceled():
                        return False

                    # QgsMessageLog.logMessage(f"Calculating {i+1}/{len(self.settings.matrix.elements)}", MESSAGE_CATEGORY, Qgis.Info)
                    self.setProgress((i + 1.0) / (len(self.settings.matrix.elements)) * 100.0)

                    element_index = i
                    i = i+1

                    route_matrix_request = RouteMatrixRequest.from_matrix_per_element(self.settings.profile,
                                                                          self.settings.matrix,
                                                                          element_index)
                    def route_matrix_callback(response: Result[RouteMatrixResponse]):
                        if not response.is_success():
                            self.data.append(RouteResult(element_index, message=response.message))
                            return

                        route_response = response.result.routes[0][0]
                        if "error_message" in route_response.feature:
                            self.data.append(RouteResult(element_index, message=route_response.feature["error_message"]))
                            return

                        self.data.append(RouteResult(element_index, route_response))

                    if network.branch_commit_id is not None:
                        public_api.post_branch_many_to_many(network.branch_commit_id, route_matrix_request, route_matrix_callback)
                    else:
                        public_api.post_snapshot_many_to_many(network.snapshot_commit_id, route_matrix_request, route_matrix_callback)

            # fetch network commit details before planning routes.
            edit_api = EditApiClient(EditApiClientSettings())
            if self.settings.network.snapshot_name is not None:
                def callback(snapshot_commit: SnapshotCommitModel):
                    plan_with_network(NetworkCommit(None, snapshot_commit.global_id))

                edit_api.get_latest_commit_for_snapshot_with_name(self.settings.network.snapshot_name, callback)
            else:
                def callback(branch_model: BranchModel):
                    plan_with_network(NetworkCommit(branch_model.commit_model.global_id))

                edit_api.get_branch(self.settings.network.branch_id, callback)

            return True
        except Exception as e:
            self.exception = e
            return False

    def finished(self, result):
        if result:
            QgsMessageLog.logMessage(f"{self.description()} finished!", MESSAGE_CATEGORY, Qgis.Info)
            self.settings.callback(self.data)
        else:
            if self.exception is None:
                QgsMessageLog.logMessage(f"{self.description()} finished without results.", MESSAGE_CATEGORY, Qgis.Info)
            else:
                QgsMessageLog.logMessage(
                    '"{name}" Exception: {exception}'.format(
                        name=self.description(),
                        exception=self.exception),
                    MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        QgsMessageLog.logMessage(f"{self.description()} was cancelled.", MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()
        RoutingTask.RUNNING_TASK = None

    RUNNING_TASKS: list['RoutingTask'] = list()
