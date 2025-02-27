from typing import Optional

from qgis._core import QgsMessageLog, Qgis, QgsVectorLayer

from ..routing.tasks.RouteResult import RouteResult
from ..routing.Matrix import Matrix
from ..settings import MESSAGE_CATEGORY
import json

class HistogramLayerBuilder(object):
    def __init__(self, layer_name: str, matrix: Matrix,  results: list[RouteResult]):
        self.layer_name = layer_name
        self.matrix = matrix
        self.results = results

    def build_layer(self, project_path: str) -> [QgsVectorLayer, QgsVectorLayer]:
        # QgsMessageLog.logMessage(f"Results in layer: {self.results}", MESSAGE_CATEGORY, Qgis.Info)

        # extract all segments.
        flattened = list()
        failed = list()
        for result in self.results:
            if not result.is_success():
                # build a feature representing the error.
                element = self.matrix.elements[result.element]
                origin_location = self.matrix.locations[element.origin]
                destination_location = self.matrix.locations[element.destination]
                error_feature = {
                            "type": "Feature",
                            "properties": {
                                "error_message": result.message,
                                "guid": f"{element.origin},{element.destination}"
                            },
                            "geometry": {
                                "type": "LineString",
                                "coordinates": [
                                    [origin_location.location.x(), origin_location.location.y() ],
                                    [destination_location.location.x(), destination_location.location.y() ]
                                ]
                            }
                        }
                failed.append(error_feature)
                # QgsMessageLog.logMessage(f"Route found with error: {error_feature}", MESSAGE_CATEGORY, Qgis.Info)
                continue

            if "features" not in result.result.feature:
                QgsMessageLog.logMessage(f"An unknown feature was found in the response", MESSAGE_CATEGORY, Qgis.Warning)
                continue

            for segment in result.result.feature["features"]:
                flattened.append(segment)

        # QgsMessageLog.logMessage(f"{flattened}", MESSAGE_CATEGORY, Qgis.Info)

        histogram: dict[str, object] = dict()
        for result in flattened:
            if result["type"] is None:
                raise Exception("Result is not a feature")

            if result["type"] == "LineString":
                continue

            if "properties" not in result:
                continue
            properties = result["properties"]
            if properties is None:
                continue

            if "_segment_guid" not in properties or properties["_segment_guid"] is None:
                continue
            segment_guid = properties["_segment_guid"]

            if "_segment_forward" not in properties or properties["_segment_forward"] is None:
                continue
            segment_forward = properties["_segment_forward"]

            count = 1
            if 'count' in properties:
                count = properties["count"]

            if segment_guid in histogram:
                histogram[segment_guid]["properties"]["count"] += count
            else:
                properties["count"] = count
                histogram[segment_guid] = result

            #QgsMessageLog.logMessage(f"{segment_guid}{segment_forward}: {result}", MESSAGE_CATEGORY, Qgis.Info)

        # write layer data as geojson
        result_layer_filename = f"{project_path}/{self.layer_name}.geojson"
        f = open(result_layer_filename, "w+")
        f.write(json.dumps({
            "type": 'FeatureCollection',
            "features": list(histogram.values())
        }))
        f.close()

        # create vector layer from geojson file.
        result_layer = QgsVectorLayer(result_layer_filename, self.layer_name, "ogr")

        #if len(failed) <= 0:
        #    return [result_layer, None]

        # write layer data as geojson
        result_layer_failed_filename = f"{project_path}/{self.layer_name}_failed.geojson"
        f = open(result_layer_failed_filename, "w+")
        f.write(json.dumps({
            "type": 'FeatureCollection',
            "features": failed
        }))
        f.close()

        # create vector layer from geojson file.
        result_failed_layer = QgsVectorLayer(result_layer_failed_filename, f"{self.layer_name}_failed", "ogr")

        return [result_layer, result_failed_layer]
