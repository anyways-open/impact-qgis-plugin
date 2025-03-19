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


    def log(self, msg):
        QgsMessageLog.logMessage(msg, MESSAGE_CATEGORY, level=Qgis.Info)


    def style_impact_outline(self, qgsLayer):
        symbols = qgsLayer.renderer().symbols(QgsRenderContext())
        sym = symbols[0]
        sym.setColor(QColor("red"))
        sym.setOpacity(0.1)
        qgsLayer.triggerRepaint()

    def style_traffic_shift_layer(self, layer, boundaries):
        # We want to have a JENKS/Natural border effect, which uses the QgsGraduatedSymbolRenderer

        ranges = []

        # This is the range for count=0
        symbol = QgsSymbol.defaultSymbol(layer.geometryType()).createSimple({'offset': '0.5'})
        symbol.setColor(QColor("#000000"))
        symbol.setWidth(1)
        rng = QgsRendererRange(-0.5, 0.5, symbol, "No difference")
        ranges.append(rng)
        
        w = 0.0
        for (lower, upper) in boundaries:
            w = w + 0.4
            
            # The positive case
            symbol = QgsSymbol.defaultSymbol(layer.geometryType()).createSimple({'offset': '0.5'})
            symbol.setColor(QColor("#ff0000"))
            symbol.setWidth(w)
            rng = QgsRendererRange(lower, upper, symbol, "Count between " + str(lower) + " and " + str(upper))
            ranges.append(rng)

            # the negative ase
            symbol = QgsSymbol.defaultSymbol(layer.geometryType()).createSimple({'offset': '0.5'})
            symbol.setColor(QColor("#0000ff"))
            symbol.setWidth(w)
            rng = QgsRendererRange(-upper, -lower, symbol, "Count between " + str(-upper) + " and " + str(-lower))
            ranges.append(rng)

        renderer = QgsGraduatedSymbolRenderer("count", ranges)
        
        paint_effects = renderer.paintEffect().effectList()
        for effect in paint_effects:
            self.log("Effect str is "+str(effect))
            if str(effect).find('QgsDropShadow') < 0:
                continue
            # effect is the dropShadowEffect
            effect.setEnabled(True)
            break
        renderer.paintEffect().setEnabled(True)
        layer.setRenderer(renderer)
        
        pal_layer = QgsPalLayerSettings()
        pal_layer.fieldName = 'count'
        pal_layer.enabled = True
        
        format = QgsTextFormat()
        format.setColor(QColor(255, 255, 255))
        format.setBlendMode(QPainter.CompositionMode_Difference)
        bufferSettings = QgsTextBufferSettings()
        bufferSettings.color = QColor(255,255,255)
        bufferSettings.setSize(1)
        bufferSettings.setEnabled(True)
        format.setBuffer(bufferSettings)
        pal_layer.setFormat(format)
        pal_layer.dist = -7
        pal_layer.mergeLines = True
        pal_layer.placement = QgsPalLayerSettings.Line
        pal_layer.placementFlags = QgsPalLayerSettings.AboveLine | QgsPalLayerSettings.AboveLine
        labels = QgsVectorLayerSimpleLabeling(pal_layer)
        layer.setLabeling(labels)

        layer.triggerRepaint()

    @staticmethod
    def style_routeplanning_layer(qgs_layer, profile_name, source_index):
        color = "#cccccc"
        offset = 1
        for key in PROFILE_COLOURS:
            if profile_name.startswith(key):
                color = PROFILE_COLOURS[key]
                offset = PROFILE_OFFSET[key]
                break
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

        # build label settings.
        layer_settings = QgsPalLayerSettings()
        text_format = QgsTextFormat()

        text_format.setFont(QFont("Arial", 12))
        text_format.setSize(12)
        text_format.setColor(QColor(color))

        # buffer_settings = QgsTextBufferSettings()
        # buffer_settings.setEnabled(True)
        # buffer_settings.setSize(1)
        # buffer_settings.setColor(QColor(color))
        #
        # text_format.setBuffer(buffer_settings)
        layer_settings.setFormat(text_format)

        layer_settings.fieldName = "count"
        layer_settings.placement = QgsPalLayerSettings.Line
        # layer_settings.placement = 2
        layer_settings.placementFlags = QgsPalLayerSettings.AboveLine

        layer_settings.enabled = True

        layer_settings = QgsVectorLayerSimpleLabeling(layer_settings)
        qgs_layer.setLabelsEnabled(True)
        qgs_layer.setLabeling(layer_settings)

        qgs_layer.triggerRepaint()
