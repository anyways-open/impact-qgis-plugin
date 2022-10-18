import json
import sys
import traceback
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QColor
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest
from qgis.core import *
from urllib import request

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
            except Exception as e:
                stack = "".join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]))
                QgsMessageLog.logMessage("Handling the response failed due to " + str(e) + "\n" + stack,
                                         'ImPact Toolbox', level=Qgis.Warning)
                QgsMessageLog.logMessage("The failed URL is " + url, 'ImPact Toolbox', level=Qgis.Warning)
                if postData is not None:
                    QgsMessageLog.logMessage("The failed Post-Data is " + json.dumps(postData), 'ImPact Toolbox',
                                             level=Qgis.Warning)
                onerror(str(e))
                if str(e) == "FIRST AID!":
                    raise e

        all_callbacks.add(callback)
        all_callbacks.add(onFinished)

        fetcher.finished.connect(lambda: onFinished(onFinished))

        req = QNetworkRequest(QUrl(url))
        for header in headers.items():
            req.setRawHeader(bytes(header[0], "UTF-8"), bytes(header[1], "UTF-8"))

        fetcher.fetchContent(req)
    except Exception as e:
        stack = "".join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]))
        QgsMessageLog.logMessage("Handling the response failed due to " + str(e) + "\n" + stack, 'ImPact Toolbox',
                                 level=Qgis.Warning)
        onerror(str(e))
        if str(e) == "FIRST AID!":
            raise e


def extract_valid_geometries(iface, features, warning='The selected layer has some entries where the geometry is Null'):
    """check if a list of feature has empty geometries. 
    :param iface (QgisInterface): the interface with the mainWindow
    :param featureLayer (QgsVectorLayer): the layer to check
    :param    warning (string, optional): a optional message to give to user if a null-geometry is found
    :return (features[]): all the features for which the geometry is valid
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


def add_reverse_lines(features):
    """
    Creates a list with both forward and backward features with `count` set correctly
    Creates list of geometries containing the original features and, for the features where rev_count > 0, a reversed feature with count=rev_count.
    
    :param features: a list of Line-features
    :return: features: a list of line-features, which contain the original features (if count > 0) and the reversed features (if count_rev > 0)
    """
    new_features = list()
    for f in features:
        new_features.append(f)
        count_rev = f["count_rev"]
        if count_rev == NULL:
            continue
        if count_rev <= 0:
            continue
        geom = f.geometry()
        nodes = geom.asPolyline()
        nodes.reverse()
        newgeom = QgsGeometry.fromPolylineXY(nodes)
        new_feature = QgsFeature(f.fields())
        new_feature.setGeometry(newgeom)
        new_feature["count"] = count_rev
        new_features.append(new_feature)

    return new_features


def generate_layer_report(features):
    """
    Creates a small piece of text giving some details about the (properties of) the features
    :param features: a list of Line-features
    """

    has_count = 0
    has_count_rev = 0
    count_is_null = 0
    count_is_zero = 0
    total_count = 0
    total_count_rev = 0
    for f in features:
        try:
            c = f["count"]
            if c == NULL:
                count_is_null += 1
            elif c == 0:
                count_is_zero += 1
            else:
                total_count += c
                has_count += 1
        except:
            pass

        try:
            rc = f["count_rev"]
            if rc == NULL:
                pass
            elif rc == 0:
                pass
            else:
                total_count_rev += rc
                has_count_rev += 1
        except:
            pass
        
    if (has_count + has_count_rev ) == 0:
        return "No lines have a field 'count' or 'count_rev' set. Nothing will be routeplanned. Select a different layer or add the appropriate values"

    total_str ="This layer contains " + str(        len(features)) + " lines. "
    forward_count_str = str( has_count) + " of these lines have the field 'count' set for a total sum of " + str(
        total_count)
    backward_count_str = "No lines have 'count_rev' set."
    if(has_count_rev > 0):
        backward_count_str =  str(has_count_rev) + " of the lines have the field 'count_rev' set for a total of " + str( total_count_rev)   
    count_rev_expl_str = "Use 'count_rev' to generate planned routes in the reverse direction of the line"
    
    has_null_str = ""
    if count_is_null > 0:
        has_null_str = "\n"+ str(count_is_null)+" of the lines have NULL as count. They will be routeplanned, but their count will be interpreted as 0"
    
    return "\n".join([total_str , forward_count_str + has_null_str, "", backward_count_str,count_rev_expl_str])


def transform_layer_to_WGS84(layer):
    """
     Cheking and transforming layers' CRS to EPSG: 4326
    :param layer: A qgis layer
    :return A list of features
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


def patch_feature(feature):
    """
    Input: a single geojson feature
    Adds a determnistic GUID to the feature
    This will modify the passed object
    @:return None
    """

    props = feature['properties']
    if feature["geometry"]["type"] != "LineString":
        # Not a linestring: we don't set a GUID
        return

    if "guid" in props:
        # GUID already set, nothing to do anymore
        return

    def clean_coord(coord):
        """
        Converts the coordinates to a standardized string. This is only used as input for the GUID
        :param coord: 
        :return: 
        """

        # Only keep the first two coordinates; a height might be provided too, but this breaks the GUID
        coord = coord[0:2]
        return ",".join(map(lambda c: str(round(c, 8)), coord))

    coords = feature["geometry"]["coordinates"]
    # Get a clean version of the coordinates
    startp = clean_coord(coords[0])
    endp = clean_coord(coords[1])
    # ... and use them as guid
    props["guid"] = startp + ";" + endp


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
        feature = {
            "type": "Feature",
            "properties": props,
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates
            }
        }
        patch_feature(feature)
        features.append(feature)
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
