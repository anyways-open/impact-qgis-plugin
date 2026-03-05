from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from qgis._core import QgsVectorLayer, QgsRenderContext, QgsSimpleLineSymbolLayer

from ..geojson.GeoJsonFeature import GeoJsonFeature
from ..routing.tasks.RouteResult import RouteResult
from ..routing.Matrix import Matrix
import json

class RoutesLayerBuilder(object):
    def __init__(self, layer_name: str, matrix: Matrix,  results: list[RouteResult]):
        self.layer_name = layer_name
        self.matrix = matrix
        self.results = results

    def build_layer(self, project_path: str) -> QgsVectorLayer:

        routes: list[GeoJsonFeature] = list()
        for result in self.results:
            if not result.is_success():
                continue

            response = result.result
            for route in response.routes:
                if route.is_error():
                    continue
                for alternative in route.alternatives:
                    coordinates: list[list[float]] = list()
                    for route_segment in alternative.segments:
                        segment = response.segments.get(route_segment.segment_id)
                        if segment is not None:
                            segment.append_coordinates(coordinates, not route_segment.forward)

                    route_feature = GeoJsonFeature({
                        "type": "Feature",
                        "properties": {

                        },
                        "geometry": {
                            "type": "LineString",
                            "coordinates": coordinates
                        }
                    })
                    routes.append(route_feature)

        # write layer data as geojson
        result_layer_filename = f"{project_path}/{self.layer_name}_routes.geojson"
        f = open(result_layer_filename, "w+")
        f.write(json.dumps(GeoJsonFeature.to_feature_collection(routes)))
        f.close()

        # create vector layer from geojson file.
        result_layer = QgsVectorLayer(result_layer_filename, f"{self.layer_name}_routes", "ogr")

        return result_layer

    @staticmethod
    def style_layer(qgs_layer: QgsVectorLayer, color: str, offset: float):
        symbols = qgs_layer.renderer().symbols(QgsRenderContext())
        sym = symbols[0]

        line_rendering = QgsSimpleLineSymbolLayer()
        line_rendering.setUseCustomDashPattern(True)
        line_rendering.setPenCapStyle(Qt.RoundCap)
        line_rendering.setOffset(0.2 * offset)

        sym.deleteSymbolLayer(0)
        sym.appendSymbolLayer(line_rendering)

        sym.setColor(QColor(color))
        sym.setWidth(1.0)

        qgs_layer.triggerRepaint()
