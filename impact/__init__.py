from qgis.core import (QgsVectorLayer, QgsRenderContext, QgsLayerTreeLayer, 
                       QgsProject, QgsPointXY, QgsCoordinateReferenceSystem, QgsCoordinateTransform)
import os, sys, json, time

def time_now():
    return time.strftime("%Y%m%d_%H%M%S") 

def write2File(filePath, content): 
    """Write a single string, list or dict to a file

    Args:
        filePath (str): the path to str output file
        content (str): the string, list of dict to write into the file.
    """
    if isinstance(content, (list, dict)):
        content = json.dumps(content)     # convert dict or lists to json-strings
    elif not isinstance(content, (str)) :
        raise Exception("Content must be string, list or dict")
    with open(filePath, 'w+') as f:
        f.write(content)

def addGeojsonsToMap(iface, fileList, Groupname="", size=1, color=None, geometrytype="LineString" ):
    """Add a series of geojson's to a map

    Args:
        iface (QgisInterface): the interface with the mainWindow
        fileList (list): list of path's to geojson files
        Groupname (str, optional): the name of the group of layers, Defaults to "".
        size (int, optional): the line width in mm. Defaults to 1 mm.
        color (QColor, optional):  the color of the output layers. Defaults to None in that case a random color is chosen.
        geometrytype (string, optional): the geometrytype of the outputlayers. Defaults to "LineString".
        
    Returns:
        (list): A list of added layers 
    """
    if len(fileList) > 1:
        root = QgsProject.instance().layerTreeRoot()
        shapeGroup = root.addGroup(Groupname) 
    
    lyrList = []
    for gjsFile in fileList:
        lyrName = os.path.basename( os.path.splitext(gjsFile)[0] )
        lyr = QgsVectorLayer('{0}|layername={1}|geometrytype=LineString'.format(gjsFile, lyrName), lyrName, "ogr")
        if len(fileList) == 1: 
            QgsProject.instance().addMapLayer(lyr)

        sym = lyr.renderer().symbols(QgsRenderContext())[0]
        if color: sym.setColor( color )
        if size: sym.setWidth( size )

        if len(fileList) > 1: 
            QgsProject.instance().addMapLayer(lyr, False)
            shapeGroup.insertChildNode(1, QgsLayerTreeLayer(lyr))
        lyr.triggerRepaint()
        lyrList.append(lyr)
    return lyrList


def qgsError(iface, message, condition=True ):
    """Raise a custom error in qgis 

    Args:
        iface (QgisInterface): the interface with the mainWindow
        message (string): the message 
        condition (bool, optional): . Defaults to True.

    Returns:
        (bool): condition
    """
    if condition:
        iface.messageBar().pushMessage('ImPact_toolbox Error', message, level=Qgis.Critical)
    return condition


def checkForNullGeometry(iface, featureLayer, warning=None ):
    """check if a feature layer  has empty geometries. 

    Args:
        iface (QgisInterface): the interface with the mainWindow
        featureLayer (QgsVectorLayer): the layer to check
        warning (string, optional): a optional message to give to user if a null-geometry is found

    Returns:
        (bool): true if a null-geometry was found. 
    """
    for feat in featureLayer.getFeatures() :
        if feat.geometry().isNull():
           if warning: iface.messageBar().pushMessage('ImPact_toolbox Warning', warning, level = Qgis.Warning)
           return True
    return False


def CrsTransformation(layer):
    """Cheking and transforming layers' CRS to EPSG: 4326"""
    if layer.crs() == 4326:
        features = layer.getFeatures()
    else:
        crsSrc = QgsCoordinateReferenceSystem(layer.crs())
        crsDest = QgsCoordinateReferenceSystem(4326)
        xform = QgsCoordinateTransform(crsSrc, crsDest, QgsProject.instance())

        features=[]
        for f in layer.getFeatures():
            g = f.geometry()
            g.transform(xform)
            f.setGeometry(g)
            features.append(f)
    return features