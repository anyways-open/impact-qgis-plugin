# -*- coding: utf-8 -*-
import json
import os
import traceback
import sys

import time

from qgis.PyQt import (QtWidgets, uic)
from qgis.core import *
from .auth.DeviceFlowAuth import DeviceFlowAuth
from .clients.api.ApiClient import ApiClient
from .clients.api.ApiClientSettings import ApiClientSettings
from .clients.api.Models.DatasetModel import DatasetLocationModel, DatasetModel, DatasetTripModel
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
from .routing.tasks.RoutingTask import RoutingTask
from .routing.tasks.RoutingTaskSettings import RoutingTaskSettings
from .impact import previous_state_tracker, default_layer_styling, staging_mode, generate_layer_report
# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ImPact_toolbox_dialog_base.ui'))


class ToolBoxDialog(QtWidgets.QDialog, FORM_CLASS):
    """
    The main dialog. All button actions get linked here with the logic in 'impact'
    """

    def __init__(self, iface, profile_keys, auth: DeviceFlowAuth, project_cache=None, parent=None):
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
        self._current_project_id = None
        self._project_cache = project_cache or {"projects": None}

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
        self.profile_picker.addItems(self.profile_keys)
        self.network_picker.currentIndexChanged.connect(self._update_routing_options_visibility)

        # Set layer filters

        self.departure_layer_picker.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.arrival_layer_picker.setFilters(QgsMapLayerProxyModel.PointLayer)

        self.movement_pairs_layer_picker.setFilters(QgsMapLayerProxyModel.LineLayer)

        # Attach button listeners
        self.perform_routeplanning_button.clicked.connect(self.run_routeplanning)

        # Hide global download button; each card has its own
        self.download_dataset_button.setVisible(False)

        # Auth button listeners
        self.login_button.clicked.connect(self.login)
        self.logout_button.clicked.connect(self.logout)
        self.auth.token_received.connect(self.on_token_received)
        self.auth.login_failed.connect(self.on_login_failed)
        self.auth.logged_out.connect(self.on_logged_out)

        # Project picker listener
        self.project_picker.currentIndexChanged.connect(self.on_project_selected)

        # Update the selected layer information
        self.movement_pairs_layer_picker.currentIndexChanged.connect(self.update_selected_layer_explanation)
        self.update_selected_layer_explanation()

        # Keep track of the last selected state of qcomboboxes
        state_tracker.init_and_connect("network_picker", self.network_picker)

        state_tracker.init_and_connect("departure_layer_picker", self.departure_layer_picker)
        state_tracker.init_and_connect("arrival_layer_picker", self.arrival_layer_picker)
        state_tracker.init_and_connect("movement_pairs_layer_picker", self.movement_pairs_layer_picker)
        state_tracker.init_and_connect("profile_picker", self.profile_picker, self.network_picker)

        # Initially hide routing options until a network is selected
        self._update_routing_options_visibility()

        # Check initial auth state (defer project fetch so dialog opens first)
        self._update_auth_ui(defer_fetch=True)

    def _update_auth_ui(self, defer_fetch=False):
        if self.auth.try_restore_session():
            name = self.auth.get_user_name() or "user"
            self.auth_status_label.setText(f"Logged in as {name}")
            self.logout_button.setEnabled(True)
            self.login_panel.setVisible(False)
            self.routeplanning_panel.setVisible(True)

            # Restore saved project immediately so network picker loads without waiting for project list
            saved_id = QgsProject.instance().readEntry("anyways", "selected_project_id")[0]
            if saved_id:
                self._current_project_id = saved_id
                self.update_network_picker()

            if defer_fetch:
                from qgis.PyQt.QtCore import QTimer
                QTimer.singleShot(0, self._fetch_projects)
            else:
                self._fetch_projects()
        else:
            self.login_panel.setVisible(True)
            self.routeplanning_panel.setVisible(False)
            self.login_button.setEnabled(True)
            self.login_code_label.setText("")

    def _update_routing_options_visibility(self):
        has_network = self.network_picker.count() > 0 and bool(self.network_picker.currentData())
        self.network_picker.setVisible(has_network)
        self.label_7.setVisible(has_network)
        self.toolbox_origin_destination_or_movement.setVisible(has_network)
        self.label_4.setVisible(has_network)
        self.project_directory.setVisible(has_network)
        self.perform_routeplanning_button.setVisible(has_network)

        self.profile_picker.setVisible(has_network)
        self.label_9.setVisible(has_network)
        self.label_10.setVisible(has_network)
        self.profile_explanation.setVisible(has_network)

        if has_network:
            # check if the selected line layer has per-feature profiles
            line_layer = self.movement_pairs_layer_picker.currentLayer()
            layer_has_profile = line_layer is not None and line_layer.fields().indexFromName("profile") > -1
            self._update_profile_picker_visibility(layer_has_profile)

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
        cached = self._project_cache.get("projects")
        if cached is not None:
            self._on_projects_loaded(cached)
            return
        try:
            self.api.get_projects(self._on_projects_loaded)
        except Exception as e:
            self.log(f"Failed to fetch projects: {e}")

    def _on_projects_loaded(self, projects):
        self._project_cache["projects"] = projects
        self.project_picker.blockSignals(True)
        self.project_picker.clear()
        self.project_picker.addItem(self.tr("Select a project..."), "")
        projects.sort(key=lambda p: p.get("lastModified") or p.get("createdAt") or "", reverse=True)
        for project in projects:
            project_id = project.get("id", "")
            project_name = project.get("name", project_id)
            org_name = project.get("_organization_name", "")
            if org_name:
                display_name = f"{org_name} / {project_name}"
            else:
                display_name = project_name
            self.project_picker.addItem(display_name, project_id)

        # Restore previously selected project
        saved_id = QgsProject.instance().readEntry("anyways", "selected_project_id")[0]
        if saved_id:
            for i in range(self.project_picker.count()):
                if self.project_picker.itemData(i) == saved_id:
                    self.project_picker.setCurrentIndex(i)
                    break
        self.project_picker.blockSignals(False)
        # Only fetch networks if a different project was selected than what's already loaded
        current_data = self.project_picker.currentData()
        if current_data and current_data != self._current_project_id:
            self.on_project_selected(self.project_picker.currentIndex())

    def on_project_selected(self, index: int):
        project_id = self.project_picker.currentData()
        if project_id:
            self._current_project_id = project_id
            QgsProject.instance().writeEntry("anyways", "selected_project_id", project_id)
            self.update_network_picker()

    def update_selected_layer_explanation(self):
        line_layer = self.movement_pairs_layer_picker.currentLayer()
        if line_layer is None:
            self.selected_layer_report.setText("No layer selected")
            self._update_profile_picker_visibility(False)
            return
        line_features = extract_valid_geometries(transform_layer_to_wgs84(line_layer))
        report = generate_layer_report(line_features)

        has_profile = line_layer.fields().indexFromName("profile") > -1
        if has_profile:
            report += "\n\nThis layer contains profile information. The profile from each trip will be used for route planning."
        self.selected_layer_report.setText(report)

        self._update_profile_picker_visibility(has_profile)

    def _update_profile_picker_visibility(self, layer_has_profile: bool):
        self.profile_picker.setEnabled(not layer_has_profile)
        self.label_10.setVisible(not layer_has_profile)
        if layer_has_profile:
            self.profile_picker.blockSignals(True)
            self.profile_picker.setCurrentIndex(-1)
            self.profile_picker.blockSignals(False)
            self.profile_explanation.setText("Profile selection is disabled because the selected layer already contains a profile attribute.")
        else:
            if self.profile_picker.currentIndex() < 0 and self.profile_picker.count() > 0:
                self.profile_picker.setCurrentIndex(0)
            self.profile_explanation.setText("(Select a profile first. The profile info will be shown here)")

    def run_routeplanning(self) -> None:
        # let user know route planning is starting
        self.perform_routeplanning_button.setEnabled(False)
        self.perform_routeplanning_button.setText(self.tr("Planning routes, please stand by..."))

        # collect the origins and destinations and build a matrix.
        source_index = self.toolbox_origin_destination_or_movement.currentIndex()

        # there are 2 different possibilities:
        # - 0: line layers with each line an origin-destination pair.
        # - 1: origin and destination point layers.
        if source_index == 0:
            line_layer = self.movement_pairs_layer_picker.currentLayer()

            if line_layer is None:
                self.error_user(self.tr("Select a linestring layer first"))
                self.perform_routeplanning_button.setEnabled(True)
                self.perform_routeplanning_button.setText(self.tr("Start route planning"))
                return

            matrix = RoutingHandler.build_matrix_from_lines(line_layer).result
        else:
            # extract geometries from the origin and destination layers.
            origin_layer = self.departure_layer_picker.currentLayer()
            destination_layer = self.arrival_layer_picker.currentLayer()

            if origin_layer is None or destination_layer is None:
                self.error_user(self.tr("Select two point layers first"))
                self.perform_routeplanning_button.setEnabled(True)
                self.perform_routeplanning_button.setText(self.tr("Start route planning"))
                return

            matrix = RoutingHandler.build_matrix_from_points(origin_layer, destination_layer).result

        # if matrix is empty, no need to continue.
        if matrix.is_empty():
            QgsMessageLog.logMessage("Could not start route planning: No data found in selected layer(s). Is there data in the layers and are the count attributes setup properly?", MESSAGE_CATEGORY, Qgis.Warning)
            self.close()
            return

        # get details about the network to use.
        network = RoutingNetwork(self.network_picker.currentData())

        # use the routing handler to do the work.
        scenario_index = self.network_picker.currentIndex()
        profile = self.profile_picker.currentText()

        time_str = time.strftime("%Y%m%d_%H%M%S")
        profile_file_name = profile.replace(".", "_")
        result_layer_name = f"scenario_{scenario_index}_{profile_file_name}_{time_str}"

        def routes_planning_callback(results: list[RouteResult]):
            self.perform_routeplanning_button.setEnabled(True)
            self.perform_routeplanning_button.setText(self.tr("Start route planning"))

            result_layer = SegmentsLayerBuilder(result_layer_name, matrix, results).build_layer(self.path)
            result_failed_layer = ErrorLayerBuilder(result_layer_name, matrix, results).build_layer(self.path)
            result_routes_layer = RoutesLayerBuilder(result_layer_name, matrix, results).build_layer(self.path)

            # determine color/offset from profile; when using per-feature profiles
            # check the first matrix element for its profile
            effective_profile = profile
            if not effective_profile and matrix.elements:
                effective_profile = matrix.elements[0].profile or ""

            color = "#cccccc"
            offset = 1
            for key in PROFILE_COLOURS:
                if effective_profile.startswith(key):
                    color = PROFILE_COLOURS[key]
                    offset = PROFILE_OFFSET[key]
                    break

            # create a group for the results.
            group = QgsProject.instance().layerTreeRoot().insertGroup(0, result_layer_name)

            # add the default results a segments layer.
            QgsProject.instance().addMapLayer(result_layer, False)
            self.layer_styling.style_routeplanning_layer(result_layer, effective_profile, scenario_index)
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

        RoutingHandler.start_route_planning(result_layer_name, network, profile, matrix, routes_planning_callback, get_token=self.auth.get_access_token)
        self.close()

    def update_network_picker(self):
        project_id = self._current_project_id or ""
        def project_callback(response_model: ResponseModel[ProjectModel]):
            picker = self.network_picker
            self.state_tracker.pause_loading()

            picker.clear()

            networks: dict[str, NetworkModel] = dict()
            for network_id in response_model.details.networks:
                network = response_model.networks[network_id]
                networks[network_id] = network

            for scenario_id in response_model.details.scenarios:
                scenario = response_model.scenarios[scenario_id]
                network = networks[scenario.network]
                name = network.name
                if picker.findText(name) < 0:
                    picker.addItem(name, network.branch)
            if picker.count() > 0:
                picker.setCurrentIndex(0)
            self.state_tracker.resume_loading()
            self._update_routing_options_visibility()

            # Populate datasets list
            self._update_dataset_list(response_model)

        if len(project_id) > 0:
            try:
                self.api.get_project(project_id, project_callback)
            except Exception as e:
                self.log(f"Failed to fetch project {project_id}: {e}")
                self._update_routing_options_visibility()

    def _update_dataset_list(self, response_model: ResponseModel[ProjectModel]):
        self.dataset_list.clear()
        self.dataset_list.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.dataset_list.setStyleSheet("QListWidget::item:hover { background: transparent; }")
        self.dataset_status_label.setText("")
        for dataset_id in response_model.details.datasets:
            if dataset_id in response_model.datasets:
                dataset = response_model.datasets[dataset_id]

                # build card widget
                card = QtWidgets.QFrame()
                card.setStyleSheet("QFrame { border: none; }")
                card_outer = QtWidgets.QHBoxLayout(card)
                card_outer.setContentsMargins(4, 6, 4, 6)
                card_outer.setSpacing(8)

                # add separator line between items
                if self.dataset_list.count() > 0:
                    sep_item = QtWidgets.QListWidgetItem()
                    sep_item.setFlags(sep_item.flags() & ~sep_item.flags())
                    sep = QtWidgets.QFrame()
                    sep.setFrameShape(QtWidgets.QFrame.HLine)
                    sep.setStyleSheet("color: #ddd;")
                    sep_item.setSizeHint(sep.sizeHint())
                    self.dataset_list.addItem(sep_item)
                    self.dataset_list.setItemWidget(sep_item, sep)

                # left: text content
                text_layout = QtWidgets.QVBoxLayout()
                text_layout.setSpacing(2)

                name_label = QtWidgets.QLabel(dataset.name)
                name_label.setStyleSheet("font-weight: bold; border: none; padding: 0;")
                text_layout.addWidget(name_label)

                if dataset.description:
                    desc_label = QtWidgets.QLabel(dataset.description)
                    desc_label.setStyleSheet("color: #555; border: none; padding: 0;")
                    desc_label.setWordWrap(True)
                    text_layout.addWidget(desc_label)

                if dataset.last_modified:
                    date_str = dataset.last_modified[:10] if len(dataset.last_modified) >= 10 else dataset.last_modified
                    date_label = QtWidgets.QLabel(f"Last modified: {date_str}")
                    date_label.setStyleSheet("color: #999; font-size: 10px; border: none; padding: 0;")
                    text_layout.addWidget(date_label)

                card_outer.addLayout(text_layout, 1)

                # right: download button
                download_btn = QtWidgets.QPushButton("Download")
                download_btn.setStyleSheet(
                    "QPushButton { border: 1px solid #aaa; border-radius: 3px; padding: 4px 12px; background: palette(button); color: white; }"
                    "QPushButton:hover { background: palette(midlight); border-color: palette(dark); }"
                    "QPushButton:pressed { background: palette(mid); }"
                    "QPushButton:disabled { color: #ccc; }"
                )
                download_btn.clicked.connect(lambda checked, did=dataset.global_id, dname=dataset.name, btn=download_btn: self._download_dataset(did, dname, btn))
                card_outer.addWidget(download_btn, 0)

                item = QtWidgets.QListWidgetItem()
                item.setSizeHint(card.sizeHint())
                self.dataset_list.addItem(item)
                self.dataset_list.setItemWidget(item, card)

    def _download_dataset(self, dataset_id: str, dataset_name: str, button: QtWidgets.QPushButton):
        button.setEnabled(False)
        button.setText(self.tr("Downloading..."))
        self.dataset_status_label.setText("")

        def on_trips_loaded(trips: list[DatasetTripModel], locations: dict[str, DatasetLocationModel]):
            button.setEnabled(True)
            button.setText("Download")

            if not trips:
                self.dataset_status_label.setText("Dataset is empty, no trips to download.")
                return

            features = []
            for trip in trips:
                if not trip.count:
                    continue
                origin_loc = locations.get(trip.origin)
                dest_loc = locations.get(trip.destination)
                if origin_loc is None or dest_loc is None:
                    continue
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [origin_loc.longitude, origin_loc.latitude],
                            [dest_loc.longitude, dest_loc.latitude]
                        ]
                    },
                    "properties": {
                        "count": trip.count,
                        "profile": trip.profile
                    }
                }
                features.append(feature)

            if not features:
                self.dataset_status_label.setText("Dataset has no trips with valid locations.")
                return

            geojson = {
                "type": "FeatureCollection",
                "features": features
            }

            import re
            safe_name = re.sub(r'[^\w\-.]', '_', dataset_name).lower()
            time_str = time.strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.path, f"dataset_{safe_name}_{time_str}.geojson")
            with open(filename, "w") as f:
                json.dump(geojson, f)

            layer_name = f"dataset_{safe_name}_{time_str}"
            layer = QgsVectorLayer(filename, layer_name, "ogr")
            QgsProject.instance().addMapLayer(layer)
            self.dataset_status_label.setText(f"Downloaded '{dataset_name}' with {len(features)} trips.")

        try:
            self.api.get_dataset(dataset_id, on_trips_loaded)
        except Exception as e:
            button.setEnabled(True)
            button.setText("Download")
            self.dataset_status_label.setText(f"Failed to download dataset: {e}")

    def log(self, msg):
        QgsMessageLog.logMessage(msg, MESSAGE_CATEGORY, level=Qgis.Info)

    def warn(self, msg):
        QgsMessageLog.logMessage(msg, MESSAGE_CATEGORY, level=Qgis.Warning)

    def error_user(self, msg, duration=60):
        self.iface.messageBar().pushMessage(u'ImPact_toolbox Error', msg, level=Qgis.Critical, duration=duration)
        stack = "".join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]))
        self.warn("Attempt to get the traceback from the latest error by error_user: "+stack)
