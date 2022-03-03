import json
from urllib import request

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QColor
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest
from qgis.core import *

standalone_mode = False
staging_mode = False

def setStandalone():
    """
    Changes the behaviour of 'fetch_blocking' and 'fetch_non_blocking' to use builin python libs instead of QGis
    :return: 
    """
    global standalone_mode
    standalone_mode = True


def fetch_blocking(url):
    """
    Gets a network resource in a synchronous way.
    If 'setStandalone' is called, uses urllib.request
    Otherwise, a QNetworkRequest and GgsBlockingNetworkRequest is used.
    
    :return: a string with the contents. Throws an exception if the resource could not be read
    """

    if standalone_mode:
        return request.urlopen(url).read().decode("UTF-8")

    blockingRequest = QgsBlockingNetworkRequest()
    result = blockingRequest.get(QNetworkRequest(QUrl(url)))

    if result != QgsBlockingNetworkRequest.NoError:
        raise Exception("Could not download " + url)

    # reply: QgsNetworkReplyContent
    reply = blockingRequest.reply()

    if reply.error() != QNetworkReply.NoError:
        raise Exception("Could not download " + url + " due to " + reply.errorString())

    qbyteArray = reply.content()
    return bytes(qbyteArray).decode("UTF-8")


all_callbacks = set()


def fetch_non_blocking(url, callback, onerror, postData=None, headers=None):
    """
    
    Fetches the requested url in a non-blocking way.
    When the data is fetched, the callback will be called with the response as single string.
    
    If postData is defined as object, then the header 'Content-Type=application/json' will be automatically set.
    The postData will be automatically serialized as JSON
    
    Note: will be _blocking_ in standalone mode too!
    :return: 
    """

    if headers is None:
        headers = {}

    if callback is None:
        raise Exception("No callback given for fetch_non_blocking")

    try:
        if postData is not None:
            if "Content-Type" not in headers:
                headers["Content-Type"] = "application/json"
            QgsMessageLog.logMessage(
                "POST-request to " + url + " with headers " + json.dumps(headers),
                'ImPact Toolbox', level=Qgis.Info)
    
            req = request.Request(url, data=json.dumps(postData).encode('UTF-8'),
                                  headers=headers)  # this will make the method "POST"
            resp = request.urlopen(req)
            raw = resp.read().decode("UTF-8")
            QgsMessageLog.logMessage(
                "POST-request to " + url + "finished")
            callback(raw)
            return
    
        if standalone_mode:
            req = request.Request(url, headers=headers)
            text = request.urlopen(req).read().decode("UTF-8")
            callback(text)
            return
    
        fetcher = QgsNetworkContentFetcher()
    
        def onFinished(self_function):
            try:
                content = fetcher.contentAsString()
                callback(content)
                all_callbacks.remove(callback)
                all_callbacks.remove(self_function)
            except Exception:
                onerror()
    
        all_callbacks.add(callback)
        all_callbacks.add(onFinished)
        
        fetcher.finished.connect(lambda: onFinished(onFinished))
    
        req = QNetworkRequest(QUrl(url))
        for header in headers.items():
            req.setRawHeader(bytes(header[0], "UTF-8"), bytes(header[1], "UTF-8"))
    
        fetcher.fetchContent(req)
    except Exception:
        onerror()

def extract_valid_geometries(iface, features, warning='The selected layer has some entries where the geometry is Null'):
    """check if a list of feature has empty geometries. 
    Args:
        iface (QgisInterface): the interface with the mainWindow
        featureLayer (QgsVectorLayer): the layer to check
        warning (string, optional): a optional message to give to user if a null-geometry is found
    Returns:
        (features[]): all the features for which the geometry is valid
    """
    valid_features = []
    fautly_features_count = 0
    for feat in features:
        if feat.geometry().isNull():
            fautly_features_count += 1
        else:
            valid_features.append(feat)

    if fautly_features_count > 0:
        iface.messageBar().pushMessage('ImPact_toolbox Warning', warning, level=Qgis.Warning)

    return valid_features


def transform_layer_to_WGS84(layer):
    """
     Cheking and transforming layers' CRS to EPSG: 4326
    :param layer: A qgis layer
    :return: A list of features
    """
    if layer.crs() == 4326:
        features = layer.getFeatures()
    else:
        crsSrc = QgsCoordinateReferenceSystem(layer.crs())
        crsDest = QgsCoordinateReferenceSystem(4326)
        xform = QgsCoordinateTransform(crsSrc, crsDest, QgsProject.instance())

        features = []
        for f in layer.getFeatures():
            g = f.geometry()
            g.transform(xform)
            f.setGeometry(g)
            features.append(f)
    return features


def extract_polygons(layer):
    pass


def lat_lon_coor(coor):
    """
    Reverses the coordinates
    :param coor: 
    :return: 
    """
    splitted = coor.split(",")
    return splitted[1] + "," + splitted[0]


def create_layergroup_from_files(filelist, groupname, color="#ff0000", width=1.0):
    root = QgsProject.instance().layerTreeRoot()
    shapeGroup = root.addGroup(groupname)  # Ater or Before (basically any name can be given to the group

    for file in filelist:
        try:
            QgsMessageLog.logMessage("Creating a layer from file " + file, 'ImPact Toolbox', level=Qgis.Info)
            fileroute = file
            filename = QgsVectorLayer(fileroute, file[:-5], "ogr")
            QgsProject.instance().addMapLayer(filename, False)
            symbols = filename.renderer().symbols(QgsRenderContext())
            sym = symbols[0]
            sym.setColor(QColor(color))
            sym.setWidth(float(width))
            filename.triggerRepaint()
            shapeGroup.insertChildNode(1, QgsLayerTreeLayer(filename))
        except Exception as e:
            QgsMessageLog.logMessage("Creating a layer from file " + file + " failed due to " + e.message,
                                     'ImPact Toolbox', level=Qgis.Warning)


def create_layer_from_file(iface, filename):
    # filepath, name in qgis, type
    lyr = QgsVectorLayer(filename, filename, "ogr")
    QgsProject.instance().addMapLayer(lyr)
    return lyr


def extract_coordinates_array(features, latlonformat=False):
    """
    Returns the coordinates of the given features as a list containing two numbers, e.g. [[4.1,51.2], [4.2,51.3], ... ]
    Returns [lon, lat] by default, unless 'latlonformat' is set
    :param features: 
    """
    result = []
    for feature in features:
        if isinstance(feature, QgsPointXY):
            point = feature
        else:
            point = feature.geometry().asPoint()
        X = point.x()
        Y = point.y()
        coor = None
        if latlonformat:
            coor = [Y, X]
        else:
            coor = [X, Y]
        result.append(coor)
    return result


def extract_coordinates(features, latlonformat=False):
    """
    Returns the coordinates of the given features as a list of strings such as "lon,lat"
    :param features: 
    """
    result = []
    for feature in features:
        if isinstance(feature, QgsPointXY):
            point = feature
        else:
            point = feature.geometry().asPoint()
        X = point.x()
        Y = point.y()
        coor = None
        if latlonformat:
            coor = str(Y) + "," + str(X)
        else:
            coor = str(X) + ',' + str(Y)
        result.append(coor)
    return result


def layer_as_geojson_features(iface, lyr):
    line_features = extract_valid_geometries(iface, transform_layer_to_WGS84(lyr))
    fields = list(map(lambda field: field.name(), lyr.fields()))
    features = []
    for qgsFeature in line_features:
        props = {}
        for fieldName in fields:
            if fieldName == "":
                continue
            val = qgsFeature.attribute(fieldName)
            if val == NULL:
                continue
            props[fieldName] = val
        gqisPoints = qgsFeature.geometry().asPolyline()
        coordinates = list(map(lambda qgisPoint: [qgisPoint[0], qgisPoint[1]], gqisPoints))
        features.append({
            "type": "Feature",
            "properties": props,
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates
            }
        })
    return features


def features_as_geojson_features(features):
    """
    Converts a list of features into a list of geojson features
    :param features: 
    :return: 
    """
    parts = []
    for feature in features:
        part = {
            "type": "Feature",
            "properties": {},
            "geometry": json.loads(feature.geometry().asJson())
        }
        parts.append(part)

    return parts
