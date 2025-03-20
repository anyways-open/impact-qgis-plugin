# -*- coding: utf-8 -*-
import json
import os
import traceback
import sys

import time

from PyQt5.QtGui import QColor
from qgis.PyQt import (QtWidgets, uic)
from qgis.core import *

from .layers.ErrorLayerBuilder import ErrorLayerBuilder
from .layers.RoutesLayerBuilder import RoutesLayerBuilder
from .routing.tasks.RouteResult import RouteResult
from .clients.publish_api.Models.RouteResponse import RouteResponse
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
from .impact import fod_api, impact_api, add_reverse_lines, \
    feature_histogram, layer_as_geojson_features, previous_state_tracker, create_layer_from_file, \
    default_layer_styling, staging_mode, patch_feature, generate_layer_report
import re
# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ImPact_toolbox_dialog_base.ui'))


class ToolBoxDialog(QtWidgets.QDialog, FORM_CLASS):
    """
    The main dialog. All button actions get linked here with the logic in 'impact'
    """

    def __init__(self, iface, profile_keys, parent=None):
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
        self.impact_api = None
        self.layer_styling = default_layer_styling.default_layer_styling()
        self.impact_api = impact_api.impact_api(None)
        state_tracker = previous_state_tracker.previous_state_tracker(QgsProject.instance())
        self.state_tracker = state_tracker

        self.profile_keys = profile_keys

        self.user_settings = QgsSettings()
        self.api_key_field.setText(self.user_settings.value("anyways.eu/impact/api_key"))
        self.current_routeplanning_task = None
        self.save_settings_button.clicked.connect(self.save_setting)
        self.save_setting()  # Fetch impact instances etc...

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
        self.impact_instance_selector.currentIndexChanged.connect(self.update_scenario_picker)
        self.save_area_outline.clicked.connect(self.save_outline_as_layer)
        self.save_impact_url_button.clicked.connect(self.save_impact_url)

        # At last: update and set the profile explanations
        self.update_scenario_picker()
        
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
        # disable components for the next version which require auth
        self.remove_auth_components()

        self.save_impact_url()  # TODO this should not be needed when login works

    def remove_auth_components(self):
        self.label.hide()
        self.api_key_field.hide()
        self.save_settings_button.hide()
        self.label_2.hide()
        self.impact_instance_selector.hide()
        self.save_area_outline.hide()

    def update_instance_picker(self, projects):
        self.log("Got " + str(len(projects)) + " projects!")
        if (len(projects) == 0):
            self.error_user(self.tr("Could not load any project file"))
            return

        clean_parts = map(lambda p: p["clientId"] + "/" + p["id"], projects)
        for clean_part in clean_parts:
            self.impact_instance_selector.addItem(clean_part)

    def clean_name(self, name):
        """
        Removes weird characters from a name, in order to use this as filename
        :param name: 
        :return: 
        """
        return re.sub(r'[<>:"/\\|?*[\]()&;]', "_",  name)

    def save_outline_as_layer(self):
        instance = self.impact_instance_selector.currentText()

        def withGeoJsonFeature(obj):
            filename = self.path + "/" + "outline_" + self.clean_name(instance) + ".geojson"
            f = open(filename, "w+")
            json.dump(
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "properties": {
                                "outline": instance
                            },
                            "geometry": obj
                        }]
                }
                , f)
            f.close()
            qgsLayer = create_layer_from_file(self.iface, filename)
            self.layer_styling.style_impact_outline(qgsLayer)
            pass

        self.impact_api.get_outline(instance, withGeoJsonFeature)

    def save_setting(self):
        self.log("Saving settings")
        api_key = self.api_key_field.text()
        self.user_settings.setValue("anyways.eu/impact/api_key", api_key)

        if api_key is not None and api_key != "":
            self.user_settings.setValue("anyways.eu/impact/api_key", "")
            self.impact_api = impact_api.impact_api(None)
            self.impact_api.load_available_projects(self.update_instance_picker, lambda e: self.error_user(
                "Could not fetch projects with this token: " + e))

    def save_impact_url(self):
        self.log("Saving impact url")
        url = self.impact_url_textfield.text()
        url = impact_api.extract_instance_name(url)
        self.impact_url_textfield.setText(url)

        self.impact_instance_selector.addItem(url)
        self.impact_instance_selector.setCurrentIndex(self.impact_instance_selector.count() - 1)
        self.update_scenario_picker()

    def query_movement_pairs(self):
        """
        The button to load movement pairs between two areas has been clicked. Lets load them!
        :return: 
        """

        self.query_movement_pairs_button.setEnabled(False)

        from_features = extract_valid_geometries(self.iface, transform_layer_to_WGS84(
            self.home_locations.currentLayer()))

        to_features = extract_valid_geometries(self.iface, transform_layer_to_WGS84(
            self.work_locations.currentLayer()))

        mode = []
        if self.include_cyclists.isChecked():
            mode.append('Bicycle')

        if self.include_car.isChecked():
            mode.append('Car')

        if self.include_train.isChecked():
            mode.append('Train')

        if self.include_public_transport.isChecked():
            mode.append('BusOrTram')

        if len(mode) == 0:
            self.error_user("Select at least one transportation mode")
            return

        fod = fod_api.fod_api()

        def withData(d):
            if len(d['features']) == 0:
                self.error_user(
                    "Nothing found in the selected area. Make sure you loaded a polygon that is big enough and is located in Flanders",
                    30)
                self.query_movement_pairs_button.setEnabled(True)
                return

            # write FOD movements in a JSON file
            timestr = time.strftime("%Y%m%d_%H%M%S")
            filename = self.path + "/" + "fod_movement_pairs_" + str.join("_", mode) + "_" + timestr + ".geojson"
            self.log("Writing movement pairs to " + filename)
            f = open(filename, "w+")
            json.dump(d, f)
            f.close()

            lyr = QgsVectorLayer(filename, "FOD Movement pairs " + str.join(" ", mode) + " " + timestr, "ogr")
            QgsProject.instance().addMapLayer(lyr)

            self.query_movement_pairs_button.setEnabled(True)
            # There is no need to return the filepath; QGis will remember this for us

        def onError(err):
            self.error_user(self.tr("Could not query the FOD-API: ") + err)
            self.query_movement_pairs_button.setEnabled(True)

        d = fod.request(from_features, to_features, withData, onError, mode)

    def check_fod_modes(self):
        mode = []
        if self.include_cyclists.isChecked():
            mode.append('Bicycle')

        if self.include_car.isChecked():
            mode.append('Car')

        if self.include_train.isChecked():
            mode.append('Train')

        if self.include_public_transport.isChecked():
            mode.append('BusOrTram')

        if len(mode) == 0:
            self.query_movement_pairs_button.setEnabled(False)
            self.query_movement_pairs_button.setText(self.tr("Please select at least one mode to query movement pairs"))
        else:
            self.query_movement_pairs_button.setEnabled(True)
            self.query_movement_pairs_button.setText(self.tr("Query movement pairs"))


    def createHistLayer(self, features, name, profile, scenario_index):
        """
        Count the segments
        :param features: segment[]
        :param name: 
        :param profile: 
        :param scenario_index: 
        :return: 
        """
        if len(features) <= 0:
            return
        
        histogram = feature_histogram.feature_histogram(features)
        geojson = histogram.to_geojson()
        
        filename = self.path + "/" + self.clean_name(name) + ".geojson"
        f = open(filename, "w+")
        f.write(json.dumps(geojson))
        f.close()

        lyr = QgsVectorLayer(filename, name, "ogr")
        QgsProject.instance().addMapLayer(lyr)
        self.layer_styling.style_routeplanning_layer(lyr, profile, scenario_index)
        # There is no need to return the filepath; QGis will remember this for us


    def createLineLayer(self, features, name, profile, scenario_index):
        """
        Creates a lineLayer based on a list of segments
        :param features: segment[][]; features[originDestinationPairIndex][segmentIndex]
        :param name: 
        :param profile: 
        :param scenario_index: 
        :return: 
        """
        
        if len(features) <= 0:
            return
        lines = list()
        for segments in features:
            coordinates = list()
            
            if len(segments) == 0:
                continue
            
            for segment in segments:
                if segment["geometry"]["type"] != "LineString":
                    continue
                
                coordinates.extend(segment["geometry"]["coordinates"][:-1])
                
            coordinates.append(segments[-1]["geometry"]["coordinates"][-1])
            
            propertiesLastSegment = segments[-1]["properties"]
            
            properties = {}
            def copyProp(key):
                if key in propertiesLastSegment:
                    if propertiesLastSegment[key] == NULL:
                        properties[key] = 0
                    else:
                        properties[key] = propertiesLastSegment[key]

            copyProp("time")
            copyProp("count")
            copyProp("distance")
            copyProp("profile")
            
            if "count" not in properties:
                properties["count"] = 1
            elif properties["count"] == 0:
                continue

            lines.append(
                {
                    "type":"Feature",
                    "properties":properties,
                    "geometry":{
                        "type":"LineString",
                        "coordinates": coordinates
                    }
                }
            )
        
        filename = self.path + "/" + self.clean_name(name) + ".geojson"
        f = open(filename, "w+")
        f.write(json.dumps({
            "type": "FeatureCollection",
            "features":lines
        }))
        f.close()

        lyr = QgsVectorLayer(filename, name, "ogr")
        QgsProject.instance().addMapLayer(lyr)
        self.layer_styling.style_routeplanning_layer(lyr, profile, scenario_index)

    def createFailLayer(self, failed_linestrings, name, profile, scenario_index):
        if len(failed_linestrings) > 0:
            self.error_user(
                self.tr("Not every requested route could be calculated; ") + str(
                    len(failed_linestrings)) + self.tr(" routes failed. A layer with failed requests has been created"))
            histogram = feature_histogram.feature_histogram(failed_linestrings)
            geojson = histogram.to_geojson()
            filename = self.path + "/" + self.clean_name(name) + ".geojson"
            f = open(filename, "w+")
            f.write(json.dumps(geojson))
            f.close()

            lyr = QgsVectorLayer(filename, name, "ogr")
            QgsProject.instance().addMapLayer(lyr)
            self.layer_styling.style_routeplanning_layer(lyr, "FAILED", scenario_index)


    def createRouteplannedLayer(self, features, failed, profile, scenario_index):
        """
        Generates the appropriate layer, based on routeplanning and the selected mergeMode
        :param features: segment[][][], with features[originIndex][notReallyDestinationIndex][segmentIndex]
        :return: 
        """
        if features is None or len(features) == 0:
            self.error_user("The requested routeplanning contained no trips", 30)
            return
        
        # If 0: create a histogram (default)
        mergemode = 0

        scenario = "live"
        if (scenario_index > 0):
            label = self.scenario_picker.currentText()
            index = label[1 + label.index(" "):]
            scenario = label[:label.index(" ")].replace("/", "_") + index


        timestr = time.strftime("%Y%m%d_%H%M%S")
       


        if mergemode == 0:
            name = "Routeplanned_hist_" + profile + "_" + scenario.replace("/", "_") + "_" + timestr
            # The 'hist layer' expects a flattened list of only segments
            flattened = list()
            for perOrigin in features:
                # results: segment[][][]
                for perDestination in perOrigin:
                    for segment in perDestination:
                        flattened.append(segment)
            self.createHistLayer(flattened , name, profile, scenario_index)
        else:
            name = "Routeplanned_lines_" + profile + "_" + scenario.replace("/", "_") + "_" + timestr
            # The line layer expects a list of trips (where trips are a list of segments)
            flattened = list()
            for perOrigin in features:
                # results: segment[][][]
                for perDestination in perOrigin:
                    flattened.append(perDestination)
            self.createLineLayer(flattened , name, profile, scenario_index)
        
    
        if (len(failed) > 0):
            
            name_failed = "Failed_" + profile + "_" + scenario.replace("/", "_") + "_" + timestr
            self.log("Creating a fail-layer with "+str(len(failed)))
            self.createFailLayer(failed, name_failed, profile, scenario_index)



    def perform_many_to_many_routeplanning(self, settings: RoutingTaskSettings, profile, from_coors, to_coors, with_routes_callback, with_failed_features_callback, prep_feature_at = None):
        """
        
        Helper method
        
        :param settings:
        :param profile: 
        :param from_coors: a list of [lon,lat] coordinates
        :param to_coors: a list of [lon,lat] coordinates
        :param scenario: 
        :param scenario_index: 
        :param with_routes_callback: Takes list of type 'features : segment[][][]', with indexing features[originIndex][destinationIndexIfNoFails][segmentIndex]
        :param with_failed_featuresperform_many_to_many_routeplanning_callback:
        :param prep_feature_at: (i: number, j: number, feature: geojson) => void. This is used e.g. to set a count on featuers at a certain position in the returned matrix
        :return: 
        """
        
        
        def routeplanning_many_to_many_done(routes):
            print("Routeplanning_many_to_many_done in ImPact_toolbox_dialog is being called")
            # features[originIndex][successFulldestinationIndex][segmentIndex]
            features = []
            failed_linestrings = []
        
            from_index = 0

            # routes["routes"] has type featureCollection[][]
            # this is a collection of features for every pair of origin/destination
            for route_list in routes["routes"]:
                to_index = 0
                perOrigin = list()
                features.append(perOrigin)
                for route in route_list:
                    perDestination = list()
                    perOrigin.append(perDestination)
                    if "error" in route:
                        self.log("from_index" + str(from_index))
                        self.log("to_index" + str(to_index))
                        err_msg = route["error_message"]
                        self.log("Route failed because of "+err_msg)
                        fromC = from_coors[from_index]
                        toC = to_coors[to_index]
                        # Something went wrong here
                        failed_linestrings.append({
                            "type": "Feature",
                            "properties": {"error_message": err_msg,
                                           "guid": str(fromC) + "," + str(toC)},
                            "geometry": {
                                "type": "LineString",
                                "coordinates": [ fromC, toC ]
                            }
                        })
                    else:
                        for feature in route["features"]:
                            if feature["geometry"]["type"] == "Point":
                                continue
        
                            patch_feature(feature)
                            if prep_feature_at is not None:
                                prep_feature_at(from_index, to_index, feature)
        
                            perDestination.append(feature)
        
                    to_index = to_index + 1
                from_index = from_index + 1

            self.log("First parsing or routeplanned routes finished, calling callbacks")

            # First the 'failed' layers, then the actual callback
            # Often, the failed layers are collected and rendered along with the actual data
            with_failed_features_callback(failed_linestrings)
            with_routes_callback(features)
            self.log("Routeplanning: callbacks have been executed. There are "+str(len(features))+" succesfull features and "+str(len(failed_linestrings))+" failed features")
    
            self.perform_routeplanning_button.setEnabled(True)
            self.perform_routeplanning_button.setText(self.tr("Perform routeplanning"))

        self.log("Requesting routes, isImpact? " + str(routing_api_obj.is_impact_backend))
        
        def onError(msg: Any) -> None:
            self.error_user(msg)
            with_routes_callback(None)

        try:
            task = RoutingTask(settings)

            QgsApplication.taskManager().addTask(task)

            routing_api_obj.request_all_routes(
                from_coors, to_coors,
                profile, routeplanning_many_to_many_done, self.error_user)
        
        except Exception as e:
            tb = ''.join(traceback.format_exception(None, e, e.__traceback__))
            self.log("ERROR: "+repr(e)+" stack trace: "+tb)
            self.log("Trying again after routing error.")
            try:
                routing_api_obj.request_all_routes(
                    from_coors, to_coors,
                    profile, routeplanning_many_to_many_done, self.error_user)
            except Exception as e:
                tb = ''.join(traceback.format_exception(None, e, e.__traceback__))
                self.log("ERROR: "+repr(e)+" stack trace: "+tb)
                self.error_user(self.tr("Planning routes failed:")+" "+str(e))
                if str(e) == "FIRST AID!":
                    raise e
                
    def update_selected_layer_explanation(self):
        line_layer = self.movement_pairs_layer_picker.currentLayer()
        if line_layer is None:
            self.selected_layer_report.setText("No layer selected")
            return
        line_features = extract_valid_geometries(transform_layer_to_wgs84(line_layer))
        report = generate_layer_report(line_features)
        self.selected_layer_report.setText(report)

    def build_matrix(self) -> Result[Matrix]:
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
                return Result()

            return RoutingHandler.build_matrix_from_points(origin_layer, destination_layer)
        else:
            line_layer = self.movement_pairs_layer_picker.currentLayer()

            if line_layer is None:
                self.error_user(self.tr("Select line layer first"))
                self.perform_routeplanning_button.setEnabled(True)
                self.perform_routeplanning_button.setText(self.tr("Start route planning"))
                return Result()

            return RoutingHandler.build_matrix_from_lines(line_layer)
            
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

    def calculate_traffic_diff(self):
        zero_layer = self.zero_situation_picker.currentLayer()
        new_layer = self.new_situation_picker.currentLayer()

        if zero_layer == new_layer:
            self.error_user(self.tr("The selected layers are the same - not much traffic shift to calculate"))
            return

        geo_features = layer_as_geojson_features(self.iface, zero_layer)
        zero_hist = feature_histogram.feature_histogram(geo_features)
        new_hist = feature_histogram.feature_histogram(layer_as_geojson_features(self.iface, new_layer))
        diff = new_hist.subtract(zero_hist)

        geojson = diff.to_geojson()
        name = "traffic_shift_between_" + zero_layer.name() + "_and_" + new_layer.name()

        filename = self.path + "/" + self.clean_name(name) + ".geojson"
        f = open(filename, "w+")
        f.write(json.dumps(geojson))
        f.close()

        lyr = QgsVectorLayer(filename, name, "ogr")
        QgsProject.instance().addMapLayer(lyr)
        self.layer_styling.style_traffic_shift_layer(lyr, diff.natural_boundaries(5))

        lyr.setLabelsEnabled(True)
        lyr.triggerRepaint()

        pass

    def update_scenario_picker(self):
        instance_name = self.impact_instance_selector.currentText()
        def withScenarioList(scenarios):
            picker = self.scenario_picker
            self.state_tracker.pause_loading()

            picker.clear()

            picker.addItem(self.tr("Plan with a recent version of OpenStreetMap"), "routing-api")

            for item in scenarios:
                name = item[0]
                branch = item[1]
                key = instance_name + " " + name
                if picker.findText(key) < 0:
                    # Item hasn't been added previously
                    picker.addItem(key, branch)
            self.state_tracker.resume_loading()

        self.impact_api.detect_scenarios(instance_name, withScenarioList)

    def log(self, msg):
        QgsMessageLog.logMessage(msg, MESSAGE_CATEGORY, level=Qgis.Info)

    def warn(self, msg):
        QgsMessageLog.logMessage(msg, MESSAGE_CATEGORY, level=Qgis.Warning)

    def warn_user(self, msg):
        iface.messageBar().pushMessage('ImPact_toolbox Warning', msg, level=Qgis.Warning)

    def error_user(self, msg, duration=60):
        self.iface.messageBar().pushMessage(u'ImPact_toolbox Error', msg, level=Qgis.Critical, duration=duration)
        stack = "".join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]))
        self.warn("Attempt to get the traceback from the latest error by error_user: "+stack)
