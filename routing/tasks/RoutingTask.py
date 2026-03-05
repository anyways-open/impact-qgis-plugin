from typing import Optional

from qgis.core import (
    QgsTask, QgsMessageLog, Qgis
)

from ...clients.publish_api.Models.AdHocRoutesResponse import AdHocRoutesResponse
from .RouteResult import RouteResult
from ...Result import Result
from ...clients.edit_api.EditApiClient import EditApiClient
from ...clients.edit_api.EditApiClientSettings import EditApiClientSettings
from ...clients.edit_api.Models.BranchModel import BranchModel
from ...clients.publish_api.PublishApiClient import PublishApiClient
from ...clients.publish_api.Models.AdHocRoutesRequest import AdHocRoutesRequest
from ...clients.publish_api.PublishApiClientSettings import PublishApiClientSettings
from ...settings import MESSAGE_CATEGORY
from .RoutingTaskSettings import RoutingTaskSettings

class RoutingTask(QgsTask):
    def __init__(self, settings: RoutingTaskSettings) -> None:
        super().__init__(f"Routing for layer {settings.name}", QgsTask.CanCancel)
        self.settings = settings
        self.data = list[RouteResult]()
        self.exception: Optional[Exception] = None

    def run(self):
        QgsMessageLog.logMessage(f"{self.description()} started!", MESSAGE_CATEGORY, Qgis.Info)

        self.setProgress(0)

        QgsMessageLog.logMessage(f"{len(self.settings.matrix.elements)} trips", MESSAGE_CATEGORY, Qgis.Info)

        try:
            # resolve branch → latest commit via Edit API
            edit_api = EditApiClient(EditApiClientSettings())
            commit_id = None

            def branch_callback(branch_model: BranchModel):
                nonlocal commit_id
                commit_id = branch_model.commit_model.global_id

            edit_api.get_branch(self.settings.network.branch_id, branch_callback)

            if commit_id is None:
                self.data.append(RouteResult(message="Failed to resolve branch to commit"))
                return True

            if self.isCanceled():
                return False

            self.setProgress(10)

            # build request with all locations and trips at once
            publish_api = PublishApiClient(PublishApiClientSettings())
            ad_hoc_request = AdHocRoutesRequest.from_matrix(self.settings.profile, self.settings.matrix)

            def route_callback(response: Result[AdHocRoutesResponse]) -> None:
                if not response.is_success():
                    self.data.append(RouteResult(message=response.message))
                    return

                self.data.append(RouteResult(result=response.result))

            publish_api.post_ad_hoc_routes(commit_id, ad_hoc_request, route_callback)

            self.setProgress(100)
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
