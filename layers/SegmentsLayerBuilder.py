from typing import Optional

from qgis._core import QgsMessageLog, Qgis, QgsVectorLayer

from ..clients.publish_api.Models.Compact.MatrixCompactResponse import MatrixCompactResponse
from ..geojson.GeoJsonFeature import GeoJsonFeature
from ..routing.tasks.RouteResult import RouteResult
from ..routing.Matrix import Matrix
from ..settings import MESSAGE_CATEGORY
import json

class SegmentsLayerBuilder(object):
    def __init__(self, layer_name: str, matrix: Matrix,  results: list[RouteResult]):
        self.layer_name = layer_name
        self.matrix = matrix
        self.results = results

    def build_layer(self, project_path: str) -> QgsVectorLayer:

        # QgsMessageLog.logMessage(f"{flattened}", MESSAGE_CATEGORY, Qgis.Info)
        histogram: dict[str, GeoJsonFeature] = dict()
        for i, result in enumerate(self.results):
            if not result.is_success():
                continue

            element = self.matrix.elements[i]

            response: MatrixCompactResponse = result.result
            for route_row in response.routes:
                for route in route_row:
                    for route_segment in route.segments:
                        segment_key = f'{route_segment.global_id}-{route_segment.forward}'

                        if segment_key not in histogram:
                            segment = response.segments[route_segment.global_id]
                            if segment is None:
                                raise RuntimeError(f"Invalid response: could not find segment {route_segment.global_id}")

                            if not route_segment.forward:
                                segment = GeoJsonFeature.reverse_linestring(segment)

                            histogram[segment_key] = segment
                        else:
                             segment = histogram[segment_key]

                        segment.add_to_attribute_value("count", element.count)
                        segment.add_or_update_attribute("id", segment_key)

            #QgsMessageLog.logMessage(f"{segment_guid}{segment_forward}: {result}", MESSAGE_CATEGORY, Qgis.Info)

        # write layer data as geojson
        result_layer_filename = f"{project_path}/{self.layer_name}.geojson"
        f = open(result_layer_filename, "w+")
        f.write(json.dumps(GeoJsonFeature.to_feature_collection(list(histogram.values()))))
        f.close()

        # create vector layer from geojson file.
        result_layer = QgsVectorLayer(result_layer_filename, self.layer_name, "ogr")

        return result_layer
