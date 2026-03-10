from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
from qgis.core import *

PROFILE_COLOURS = {
    "bicycle": "#2222cc",
    "pedestrian": "#22cc22",
    "car": "#bb2222",
    "bigtruck": "#333333",
    "FAILED": "#ff0000"
}

PROFILE_OFFSET = {
    "bicycle": 2,
    "pedestrian": 3,
    "car": 1,
    "bigtruck": 1,
    "FAILED": 0
}


class default_layer_styling:

    def __init__(self):
        pass


    @staticmethod
    def style_routeplanning_layer(qgs_layer, profile_name, source_index):
        color = "#cccccc"
        offset = 1
        for key in PROFILE_COLOURS:
            if profile_name.startswith(key):
                color = PROFILE_COLOURS[key]
                offset = PROFILE_OFFSET[key]
                break
        renderer = qgs_layer.renderer()
        if renderer is None:
            return
        symbols = renderer.symbols(QgsRenderContext())
        if not symbols:
            return
        sym = symbols[0]

        line_rendering = QgsSimpleLineSymbolLayer()
        line_rendering.setUseCustomDashPattern(True)
        line_rendering.setPenCapStyle(Qt.RoundCap)
        line_rendering.setOffset(1.0 * offset)

        sym.deleteSymbolLayer(0)
        sym.appendSymbolLayer(line_rendering)

        sym.setColor(QColor(color))
        sym.setWidth(1.0)

        # build label settings.
        layer_settings = QgsPalLayerSettings()
        text_format = QgsTextFormat()

        text_format.setFont(QFont("Arial", 12))
        text_format.setSize(12)
        text_format.setColor(QColor(color))

        buffer_settings = QgsTextBufferSettings()
        buffer_settings.setEnabled(True)
        buffer_settings.setSize(1)
        buffer_settings.setColor(QColor("#ffffff"))
        text_format.setBuffer(buffer_settings)
        layer_settings.setFormat(text_format)

        layer_settings.fieldName = "count"
        layer_settings.placement = QgsPalLayerSettings.Line
        layer_settings.placementFlags = QgsPalLayerSettings.BelowLine
        layer_settings.dist = 1.0

        layer_settings.enabled = True

        layer_settings = QgsVectorLayerSimpleLabeling(layer_settings)
        qgs_layer.setLabelsEnabled(True)
        qgs_layer.setLabeling(layer_settings)

        qgs_layer.triggerRepaint()
