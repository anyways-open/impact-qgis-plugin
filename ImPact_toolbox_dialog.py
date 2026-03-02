# -*- coding: utf-8 -*-
import os
import traceback
import sys

import time

from qgis.PyQt import (QtWidgets, uic)
from qgis.core import *
from urllib.parse import urlparse

from .auth.DeviceFlowAuth import DeviceFlowAuth
from .clients.api.ApiClient import ApiClient
from .clients.api.ApiClientSettings import ApiClientSettings
from .clients.api.Models.NetworkModel import NetworkModel
from .clients.api.Models.ProjectModel import ProjectModel
from .clients.api.Models.ResponseModel import ResponseModel
from .layers.ErrorLayerBuilder import ErrorLayerBuilder
from .layers.RoutesLayerBuilder import RoutesLayerBuilder
from .routing.tasks.RouteResult import RouteResult
from .layers.SegmentsLayerBuilder import SegmentsLayerBuilder
from .settings import MESSAGE_CATEGORY, PROFILE_COLOURS, PROFILE_OFFSET
from .Result import Result
from .layers.PointLayerHelpers import extract_coordinates_array, extract_valid_geometries, transform_layer_to_wgs84
from .routing.Matrix import Matrix
from .routing.RoutingHandler import RoutingHandler
from .routing.RoutingNetwork import RoutingNetwork
from .settings import SNAPSHOT_NAME
from .routing.tasks.RoutingTask import RoutingTask
from .routing.tasks.RoutingTaskSettings import RoutingTaskSettings, NetworkCommit
from .impact import previous_state_tracker, default_layer_styling, staging_mode, generate_layer_report
# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ImPact_toolbox_dialog_base.ui'))


class ToolBoxDialog(QtWidgets.QDialog, FORM_CLASS):
    """
    The main dialog. All button actions get linked here with the logic in 'impact'
    """

    def __init__(self, iface, profile_keys, auth: DeviceFlowAuth, parent=None):
        """Constructor."""
        super(ToolBoxDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect

       # QCoreApplication.installTranslator("")
        self.setupUi(self)
        self.setModal(True)

        if staging_mode:
            self.warn("Debug build using ANYWAYS testing server")

        self.log("Staging mode: "+str(staging_mode))

        self.iface = iface
        self.layer_styling = default_layer_styling.default_layer_styling()
        state_tracker = previous_state_tracker.previous_state_tracker(QgsProject.instance())
        self.state_tracker = state_tracker

        self.profile_keys = profile_keys
        self.auth = auth

        self.api = ApiClient(ApiClientSettings(), get_token=self.auth.get_access_token)

        self.user_settings = QgsSettings()
        self.current_routeplanning_task = None

        # Get project path
        prjpath = QgsProject.instance().fileName()
        if (not os.path.isdir(prjpath)):
            prjpath = os.path.dirname(prjpath)
        self.project_directory.setFilePath(prjpath)
        self.project_directory.setEnabled(False)
        self.path = prjpath

        # Set routing api options
        self.scenario_picker.addItem(self.tr("Plan with a recent version of OpenStreetMap"), "routing-api")
        self.profile_picker.addItems(self.profile_keys)

        # Set layer filters

        self.departure_layer_picker.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.arrival_layer_picker.setFilters(QgsMapLayerProxyModel.PointLayer)

        self.movement_pairs_layer_picker.setFilters(QgsMapLayerProxyModel.LineLayer)

        # Attach button listeners
        self.perform_routeplanning_button.clicked.connect(self.run_routeplanning)
        self.impact_instance_selector.currentIndexChanged.connect(self.update_network_picker)
        self.save_impact_url_button.clicked.connect(self.save_impact_url)

        # Auth button listeners
        self.login_button.clicked.connect(self.login)
        self.logout_button.clicked.connect(self.logout)
        self.auth.token_received.connect(self.on_token_received)
        self.auth.login_failed.connect(self.on_login_failed)
        self.auth.logged_out.connect(self.on_logged_out)

        # Project picker listener
        self.project_picker.currentIndexChanged.connect(self.on_project_selected)

        # At last: update and set the profile explanations
        self.update_network_picker()

        # Update the selected layer information
        self.movement_pairs_layer_picker.currentIndexChanged.connect(self.update_selected_layer_explanation)
        self.update_selected_layer_explanation()

        # Keep track of the last selected state of qcomboboxes
        state_tracker.init_and_connect("impact_instance_selector", self.impact_instance_selector)
        state_tracker.init_and_connect("scenario_picker", self.scenario_picker)

        state_tracker.init_and_connect("departure_layer_picker", self.departure_layer_picker)
        state_tracker.init_and_connect("arrival_layer_picker", self.arrival_layer_picker)
        state_tracker.init_and_connect("movement_pairs_layer_picker", self.movement_pairs_layer_picker)
        state_tracker.init_and_connect("profile_picker", self.profile_picker, self.scenario_picker)
        state_tracker.init_and_connect_textfield("impact_url", self.impact_url_textfield)

        # Check initial auth state
        self._update_auth_ui()

        self.save_impact_url()  # TODO this should not be needed when login works

    def _update_auth_ui(self):
        if self.auth.is_logged_in:
            name = self.auth.get_user_name() or "user"
            self.auth_status_label.setText(f"Logged in as {name}")
            self.login_button.setEnabled(False)
            self.logout_button.setEnabled(True)
            self.login_code_label.setText("")
            self.project_picker.setEnabled(True)
            self._fetch_projects()
        else:
            self.auth_status_label.setText("Not logged in")
            self.login_button.setEnabled(True)
            self.logout_button.setEnabled(False)
            self.login_code_label.setText("")
            self.project_picker.setEnabled(False)
            self.project_picker.clear()

    def login(self):
        self.login_button.setEnabled(False)
        self.login_code_label.setText("Connecting to identity server...")

        flow = self.auth.start_device_flow()
        if flow is None:
            self.login_button.setEnabled(True)
            return

        user_code = flow.get("user_code", "")
        verification_uri = flow.get("verification_uri", "")
        self.login_code_label.setText(
            f"A browser window has been opened. If it didn't open, visit:\n"
            f"{verification_uri}\n\n"
            f"Enter code: {user_code}"
        )

    def on_token_received(self, access_token: str):
        self._update_auth_ui()

    def on_login_failed(self, error_message: str):
        self.login_button.setEnabled(True)
        self.login_code_label.setText(f"Login failed: {error_message}")

    def logout(self):
        self.auth.logout()

    def on_logged_out(self):
        self._update_auth_ui()

    def _fetch_projects(self):
        try:
            self.api.get_projects(self._on_projects_loaded)
        except Exception as e:
            self.log(f"Failed to fetch projects: {e}")

    def _on_projects_loaded(self, projects: list[dict]):
        self.project_picker.clear()
        self.project_picker.addItem(self.tr("Select a project..."), "")
        for project in projects:
            project_id = project.get("id", "")
            project_name = project.get("name", project_id)
            self.project_picker.addItem(project_name, project_id)

    def on_project_selected(self, index: int):
        project_id = self.project_picker.currentData()
        if project_id:
            self.impact_instance_selector.clear()
            self.impact_instance_selector.addItem(project_id)
            self.impact_instance_selector.setCurrentIndex(0)
            self.update_network_picker()

    @staticmethod
    def extract_instance_name(url: str):
        if not url.startswith("http"):
            return url
        path = urlparse(url).path[1:]
        parts = list(filter(lambda s: s != "", path.split("/")))
        if parts[0] == 'impact':
            del parts[0]
        try:
            int(parts[-1])
            del parts[-1]
        except:
            pass

        return parts[-1]

    def save_impact_url(self):
        self.log("Saving impact url")
        url = self.impact_url_textfield.text()
        url = self.extract_instance_name(url)
        self.impact_url_textfield.setText(url)

        self.impact_instance_selector.addItem(url)
        self.impact_instance_selector.setCurrentIndex(self.impact_instance_selector.count() - 1)
        self.update_network_picker()

    def update_selected_layer_explanation(self):
        line_layer = self.movement_pairs_layer_picker.currentLayer()
        if line_layer is None:
            self.selected_layer_report.setText("No layer selected")
            return
        line_features = extract_valid_geometries(transform_layer_to_wgs84(line_layer))
        report = generate_layer_report(line_features)
        self.selected_layer_report.setText(report)

    def run_routeplanning(self) -> None:
        # let user know route planning is starting
        self.perform_routeplanning_button.setEnabled(False)
        self.perform_routeplanning_button.setText(self.tr("Planning routes, please stand by..."))

        # collect the origins and destinations and build a matrix.
        source_index = self.toolbox_origin_destination_or_movement.currentIndex()

        # there are 2 different possibilities:
        # - 0: origin and destination point layers.
        # - 1: line layers with each line an origin-destination pair.
        if source_index == 0:
            # extract geometries from the origin and destination layers.
            origin_layer = self.departure_layer_picker.currentLayer()
            destination_layer = self.arrival_layer_picker.currentLayer()

            if origin_layer is None or destination_layer is None:
                self.error_user(self.tr("Select two point layers first"))
                self.perform_routeplanning_button.setEnabled(True)
                self.perform_routeplanning_button.setText(self.tr("Start route planning"))
                return

            matrix = RoutingHandler.build_matrix_from_points(origin_layer, destination_layer).result
        else:
            line_layer = self.movement_pairs_layer_picker.currentLayer()

            if line_layer is None:
                self.error_user(self.tr("Select line layer first"))
                self.perform_routeplanning_button.setEnabled(True)
                self.perform_routeplanning_button.setText(self.tr("Start route planning"))
                return

            matrix = RoutingHandler.build_matrix_from_lines(line_layer).result

        # if matrix is empty, no need to continue.
        if matrix.is_empty():
            QgsMessageLog.logMessage("Could not start route planning: No data found in selected layer(s). Is there data in the layers and are the count attributes setup properly?", MESSAGE_CATEGORY, Qgis.Warning)
            self.close()
            return

        # get details about the network to use.
        if self.scenario_picker.currentIndex() == 0:
            # use the latest snapshot.
            network = RoutingNetwork(SNAPSHOT_NAME)
        else:
            # use the branch, get the latest commit.
            network = RoutingNetwork(None, self.scenario_picker.currentData())

        # use the routing handler to do the work.
        scenario_index = self.scenario_picker.currentIndex()
        profile = self.profile_picker.currentText()

        time_str = time.strftime("%Y%m%d_%H%M%S")
        profile_file_name = profile.replace(".", "_")
        result_layer_name = f"live_{profile_file_name}_{time_str}"
        if scenario_index > 0:
            result_layer_name = f"scenario_{scenario_index-1}_{profile_file_name}_{time_str}"

        def routes_planning_callback(results: list[RouteResult]):
            self.perform_routeplanning_button.setEnabled(True)
            self.perform_routeplanning_button.setText(self.tr("Start route planning"))

            result_layer = SegmentsLayerBuilder(result_layer_name, matrix, results).build_layer(self.path)
            result_failed_layer = ErrorLayerBuilder(result_layer_name, matrix, results).build_layer(self.path)
            result_routes_layer = RoutesLayerBuilder(result_layer_name, matrix, results).build_layer(self.path)

            color = "#cccccc"
            offset = 1
            for key in PROFILE_COLOURS:
                if profile.startswith(key):
                    color = PROFILE_COLOURS[key]
                    offset = PROFILE_OFFSET[key]
                    break

            # create a group for the results.
            group = QgsProject.instance().layerTreeRoot().insertGroup(0, result_layer_name)

            # add the default results a segments layer.
            QgsProject.instance().addMapLayer(result_layer, False)
            self.layer_styling.style_routeplanning_layer(result_layer, profile, scenario_index)
            group.addLayer(result_layer)

            # add routes layer, style it but set it invisible.
            QgsProject.instance().addMapLayer(result_routes_layer, False)
            RoutesLayerBuilder.style_layer(result_routes_layer, color, offset)
            group.addLayer(result_routes_layer)
            group.findLayer(result_routes_layer).setItemVisibilityChecked(False)

            # add error layer, if any.
            if result_failed_layer is not None:
                QgsProject.instance().addMapLayer(result_failed_layer, False)
                self.layer_styling.style_routeplanning_layer(result_failed_layer, "FAILED", scenario_index)
                group.addLayer(result_failed_layer)
            return

        RoutingHandler.start_route_planning(result_layer_name, network, profile, matrix, routes_planning_callback)
        self.close()

    def update_network_picker(self):
        project_id = self.impact_instance_selector.currentText()
        def project_callback(response_model: ResponseModel[ProjectModel]):
            picker = self.scenario_picker
            self.state_tracker.pause_loading()

            picker.clear()

            picker.addItem(self.tr("Plan with a recent version of OpenStreetMap"), "routing-api")

            networks: dict[str, NetworkModel] = dict()
            for network_id in response_model.details.networks:
                network = response_model.networks[network_id]
                networks[network_id] = network

            for scenario_id in response_model.details.scenarios:
                scenario = response_model.scenarios[scenario_id]
                network = networks[scenario.network]
                network.name = f'{network.name} - {scenario.name}'

            for network in networks.values():
                name = network.name
                branch = network.branch
                key = f'{name}'
                if picker.findText(key) < 0:
                    picker.addItem(key, branch)
            self.state_tracker.resume_loading()

        if len(project_id) > 0:
            self.api.get_project(project_id, project_callback)

    def log(self, msg):
        QgsMessageLog.logMessage(msg, MESSAGE_CATEGORY, level=Qgis.Info)

    def warn(self, msg):
        QgsMessageLog.logMessage(msg, MESSAGE_CATEGORY, level=Qgis.Warning)

    def error_user(self, msg, duration=60):
        self.iface.messageBar().pushMessage(u'ImPact_toolbox Error', msg, level=Qgis.Critical, duration=duration)
        stack = "".join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]))
        self.warn("Attempt to get the traceback from the latest error by error_user: "+stack)
