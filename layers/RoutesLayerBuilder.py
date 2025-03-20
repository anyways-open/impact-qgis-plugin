from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from qgis._core import QgsMessageLog, Qgis, QgsVectorLayer, QgsFeature, QgsRenderContext, QgsSimpleLineSymbolLayer, \
    QgsPalLayerSettings, QgsTextFormat, QgsVectorLayerSimpleLabeling

from ..clients.publish_api.Models.Compact.MatrixCompactResponse import MatrixCompactResponse
from ..geojson.GeoJsonFeature import GeoJsonFeature
from ..routing.tasks.RouteResult import RouteResult
from ..routing.Matrix import Matrix
from ..settings import MESSAGE_CATEGORY
import json

class RoutesLayerBuilder(object):
    def __init__(self, layer_name: str, matrix: Matrix,  results: list[RouteResult]):
        self.layer_name = layer_name
        self.matrix = matrix
        self.results = results

    def build_layer(self, project_path: str) -> QgsVectorLayer:

        # QgsMessageLog.logMessage(f"{flattened}", MESSAGE_CATEGORY, Qgis.Info)
        routes: list[GeoJsonFeature] = list()
        for result in self.results:
            if not result.is_success():
                continue

            response: MatrixCompactResponse = result.result
            for route_row in response.routes:
                for route in route_row:
                    coordinates: list[list[float]] = list()
                    for route_segment in route.segments:
                        segment = response.segments[route_segment.global_id]
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

            #QgsMessageLog.logMessage(f"{segment_guid}{segment_forward}: {result}", MESSAGE_CATEGORY, Qgis.Info)

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

        # # build label settings.
        # layer_settings = QgsPalLayerSettings()
        # text_format = QgsTextFormat()
        #
        # text_format.setFont(QFont("Arial", 12))
        # text_format.setSize(12)
        # text_format.setColor(QColor(color))

        # buffer_settings = QgsTextBufferSettings()
        # buffer_settings.setEnabled(True)
        # buffer_settings.setSize(1)
        # buffer_settings.setColor(QColor(color))
        #
        # text_format.setBuffer(buffer_settings)
        # layer_settings.setFormat(text_format)
        #
        # layer_settings.fieldName = "count"
        # layer_settings.placement = QgsPalLayerSettings.Line
        # # layer_settings.placement = 2
        # layer_settings.placementFlags = QgsPalLayerSettings.AboveLine
        #
        # layer_settings.enabled = True
        #
        # layer_settings = QgsVectorLayerSimpleLabeling(layer_settings)
        # qgs_layer.setLabelsEnabled(True)
        # qgs_layer.setLabeling(layer_settings)

        qgs_layer.triggerRepaint()

