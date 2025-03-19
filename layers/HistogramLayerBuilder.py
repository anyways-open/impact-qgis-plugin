from typing import Optional

from qgis._core import QgsMessageLog, Qgis, QgsVectorLayer

from ..clients.publish_api.Models.Compact.MatrixCompactResponse import MatrixCompactResponse
from ..geojson.GeoJsonFeature import GeoJsonFeature
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

        # build failed layer if needed.
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

        # QgsMessageLog.logMessage(f"{flattened}", MESSAGE_CATEGORY, Qgis.Info)
        histogram: dict[str, GeoJsonFeature] = dict()
        for result in self.results:
            if not result.is_success():
                continue

            response: MatrixCompactResponse = result.result
            for route_row in response.routes:
                for route in route_row:
                    for route_segment in route.segments:
                        segment_key = f'{route_segment.global_id}-{route_segment.forward}'

                        if segment_key not in histogram:
                            segment = response.segments[route_segment.global_id]
                            if segment is None:
                                raise RuntimeError(f"Invalid response: could not find segment {route_segment.global_id}")

                            if route_segment.forward:
                                histogram[segment_key] = segment
                            else:
                                histogram[segment_key] = GeoJsonFeature.reverse_linestring(segment)

                        else:
                             segment = histogram[segment_key]

                        segment.add_to_attribute_value("count", 1)

            #QgsMessageLog.logMessage(f"{segment_guid}{segment_forward}: {result}", MESSAGE_CATEGORY, Qgis.Info)

        # write layer data as geojson
        result_layer_filename = f"{project_path}/{self.layer_name}.geojson"
        f = open(result_layer_filename, "w+")
        f.write(json.dumps(GeoJsonFeature.to_feature_collection(list(histogram.values()))))
        f.close()

        # create vector layer from geojson file.
        result_layer = QgsVectorLayer(result_layer_filename, self.layer_name, "ogr")

        if len(failed) <= 0:
            return [result_layer, None]

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
