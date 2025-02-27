from qgis._core import QgsPointXY, QgsMessageLog, Qgis, QgsCoordinateReferenceSystem, QgsCoordinateTransform, \
    QgsProject, QgsVectorLayer, QgsFeature

from ..settings import MESSAGE_CATEGORY


def extract_coordinates_array(features) -> list[list[float]]:
    """
    Returns the coordinates of the given features as a list containing two numbers, e.g. [[4.1,51.2], [4.2,51.3], ... ]
    :param features:
    """
    result = []
    for feature in features:
        if isinstance(feature, QgsPointXY):
            point = feature
        else:
            point = feature.geometry().asPoint()

        result.append([point.x(), point.y()])
    return result

def extract_valid_geometries(features: list[QgsFeature]) -> list[QgsFeature]:
    valid_features = []
    faulty_features_count = 0
    for feat in features:
        if feat.geometry().isNull():
            faulty_features_count += 1
        else:
            valid_features.append(feat)

    if faulty_features_count > 0:
        QgsMessageLog.logMessage("Layer has features that are invalid", MESSAGE_CATEGORY, Qgis.Warning)

    return valid_features

def transform_layer_to_wgs84(layer: QgsVectorLayer) -> list[QgsFeature]:
    """
     Checking and transforming layers' CRS to EPSG: 4326
    :param layer: A qgis layer
    :return A list of features
    """
    if layer.crs() == 4326:
        features = layer.getFeatures()
    else:
        crs_src = QgsCoordinateReferenceSystem(layer.crs())
        crs_dest = QgsCoordinateReferenceSystem.fromEpsgId(4326)
        xform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())

        features = []
        for f in layer.getFeatures():
            g = f.geometry()
            g.transform(xform)
            f.setGeometry(g)
            features.append(f)
    return features