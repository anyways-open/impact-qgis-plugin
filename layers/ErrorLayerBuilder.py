from typing import Union

from qgis._core import QgsVectorLayer

from ..routing.tasks.RouteResult import RouteResult
from ..routing.Matrix import Matrix
import json

class ErrorLayerBuilder(object):
    def __init__(self, layer_name: str, matrix: Matrix,  results: list[RouteResult]):
        self.layer_name = layer_name
        self.matrix = matrix
        self.results = results

    def build_layer(self, project_path: str) -> Union[QgsVectorLayer, None]:
        failed = list()

        for result in self.results:
            if not result.is_success():
                # entire request failed
                error_feature = {
                    "type": "Feature",
                    "properties": {
                        "error_message": result.message,
                        "guid": "request_error"
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[0, 0], [0, 0]]
                    }
                }
                failed.append(error_feature)
                continue

            # check individual routes for errors
            response = result.result
            for route_idx, route in enumerate(response.routes):
                if route.is_error():
                    element = self.matrix.elements[route_idx]
                    origin_location = self.matrix.locations[element.origin]
                    destination_location = self.matrix.locations[element.destination]
                    error_feature = {
                        "type": "Feature",
                        "properties": {
                            "error_message": route.error,
                            "guid": f"{element.origin},{element.destination}"
                        },
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [
                                [origin_location.location.x(), origin_location.location.y()],
                                [destination_location.location.x(), destination_location.location.y()]
                            ]
                        }
                    }
                    failed.append(error_feature)

        if len(failed) <= 0:
            return None

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

        return result_failed_layer
