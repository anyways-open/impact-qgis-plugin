# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ToolBox
                                 A QGIS plugin
 This plugin is a suite of tools for the Impact Analysis
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-07-27
        git sha              : $Format:%H$
        copyright            : (C) 2020 by Hamed Eftekhar @ ANYWAYS
        email                : hamed@anyways.eu
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, qVersion
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox 
from qgis.core import *
from qgis.utils import iface
from qgis.gui import QgsMessageBar

# Initialize Qt resources from file resources.py
from .resources_rc import *
# Import the code for the dialog
from .ImPact_toolbox_dialog import ToolBoxDialog
import sys, os.path, json, shutil, time, asyncio, os
import requests

#module for this tool
from .impact import routing, addGeojsonsToMap, checkForNullGeometry, qgsError, write2File, time_now,CrsTransformation

#TODO: refactor 
#import pandas as pd
#import aiohttp
#import backoff


class ToolBox:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', 'ToolBox_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Impact toolbox')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('ToolBox', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/ImPact_toolbox/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Impact ToolBox'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Impact toolbox'),
                action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = ToolBoxDialog()
            self._r = routing.routing()

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # if OK was pressed
        if result:
            KEY = self.dlg.routingTab_KeyHolder.text()
                
            #save hey in a txtfile
            PATH=os.path.dirname(os.path.realpath(__file__))
            with open (PATH+"/API_Key.txt", "w") as text_file:
                print(KEY, file=text_file)

            if self.dlg.toolBox.currentIndex() == 0:            # ROUTING        
                if self.dlg.routingWgt.currentIndex() == 0:        # ROUTING ALL POI's 

                    # get vars from UI
                    ODLayer = self.dlg.routingTab1_mLayers.currentLayer()
                    path = self.dlg.routingTab1_outDirTxt.text()
                    PROFILE = self.dlg.routingTab1_profileCbx.currentText().lower()
                    size = self.dlg.routingTab1_widthNum.value()
                    color =  self.dlg.routingTab1_mColorBtn.color()
                    sepRoutes = self.dlg.routingtab1_SepRoutes_Cbx.isChecked()

                    #other variabels 
                    gjsList = []
                    fileList = []
                    POIs = [ { 'id': f[0], 'xy': [f.geometry().asPoint().x(),  f.geometry().asPoint().y()] }
                               for f in CrsTransformation(ODLayer) if f.geometry().isNull() == False ]

                    #WARN if file has null-geometries
                    checkForNullGeometry(self.iface, ODLayer, self.tr('The POIs Layer has Null geometries!') )

                    #loop trought all poi's. 
                    for from_poi in POIs: 
                        for to_poi in POIs: 
                            if from_poi == to_poi: continue
                            
                            #make http request, response is in geojson format
                            response = self._r.fromto(from_poi['xy'] , to_poi['xy'] , KEY , PROFILE)  

                            from_id  = str( from_poi['id'] )
                            to_id    = str(  to_poi['id']  )
                            O_D      = "{0}_{1}".format( from_poi['id'], to_poi['id'] )
                            if ('features' in response) == False or len(response['features']) == 0:
                                response = { "type": 'FeatureCollection',
                                        "features":[{'type': 'Feature', 'name': 'ShapeMeta',
                                               'properties': {'name': 'N/A', 'highway': 'N/A', 'profile': PROFILE, 
                                               'From': from_id, 'To':  to_id, 'O_D': O_D } 
                                            }] }
                            else:
                                for n in range(len(response['features'])):
                                    response['features'][n]['properties']['From'] = from_id
                                    response['features'][n]['properties']['To']   = to_id
                                    response['features'][n]['properties']['O_D']  = O_D
                            gjsList.append(response)
                    #TODO handle http errors

                    if sepRoutes:    # routing All POI's WITH separated routes
                        for gjs in gjsList:
                            from_poi_id = gjs['features'][0]['properties']['From']
                            to_poi_id = gjs['features'][0]['properties']['To'] 
                            outName = path + "/{0}_to_{1}_by_{2}.json".format(from_poi_id, to_poi_id, PROFILE.upper() ) 
                            write2File(outName, gjs)
                            fileList.append(outName)
                    else:                                                 # routing All POI's NO separated routes     
                        #map responses into one geojson
                        gjs = { "type": 'FeatureCollection',  "features": []}
                        for item in  gjsList: 
                            gjs['features'] += item['features']

                        #Write output
                        outName =  path + "/Routings_by_{0}_{1}.json".format(PROFILE.upper(), time_now() ) 
                        write2File(outName, gjs)
                        fileList = [outName]

                    # add to map
                    groupName = PROFILE.upper() + "_Routings"
                    addGeojsonsToMap(self.iface, fileList, groupName, size, color )

                elif self.dlg.routingWgt.currentIndex() == 1:      # ROUTING Origins to Destinations
                
                    # get vars from UI
                    OLayer =  self.dlg.routingTab2_O_mLayers.currentLayer()
                    DLayer =  self.dlg.routingTab2_D_mLayers.currentLayer()
                    path =    self.dlg.routingTab2_outDirTxt.text()
                    PROFILE = self.dlg.routingTab2_profileCbx.currentText().lower()
                    size =    self.dlg.routingTab2_widthNum.value()
                    color =   self.dlg.routingTab2_mColorBtn.color()
                    sepRoutes = self.dlg.routingtab2_SepRoutes_Cbx.isChecked()

                    #other variabels                   
                    gjsList = []
                    fileList = []
                    O_POIs = [ { 'id': f[0], 'xy': [f.geometry().asPoint().x(),  f.geometry().asPoint().y()] }
                               for f in CrsTransformation(OLayer) if f.geometry().isNull() == False ]
                    D_POIs = [ { 'id': f[0], 'xy': [f.geometry().asPoint().x(),  f.geometry().asPoint().y()] }
                               for f in CrsTransformation(DLayer) if f.geometry().isNull() == False ]

                    #WARN if file has null-geometries
                    checkForNullGeometry(self.iface, OLayer, self.tr("The origin POI's Layer has Null geometries!") )
                    checkForNullGeometry(self.iface, DLayer, self.tr("The destination POI's Layer has Null geometries!") )

                    #loop trought all poi's. 
                    for from_poi in O_POIs: 
                        for to_poi in D_POIs: 
                            response = self._r.fromto(from_poi['xy'] , to_poi['xy'] , KEY , PROFILE)  # http request, response is in geojson format

                            from_id  = str( from_poi['id'] )
                            to_id    = str(  to_poi['id']  )
                            O_D      = "{0}_{1}".format( from_poi['id'], to_poi['id'] )
                            if ('features' in response) == False or len(response['features']) == 0:
                                response = { "type": 'FeatureCollection',
                                        "features":[{'type': 'Feature', 'name': 'ShapeMeta',
                                               'properties': {'name': 'N/A', 'highway': 'N/A', 'profile': PROFILE, 
                                               'From': from_id, 'To':  to_id, 'O_D': O_D } 
                                            }] }
                            else:
                                for n in range(len(response['features'])):
                                    response['features'][n]['properties']['From'] = from_id
                                    response['features'][n]['properties']['To']   = to_id
                                    response['features'][n]['properties']['O_D']  = O_D
                            gjsList.append(response)
                    #TODO handle http errors

                    if sepRoutes:  # Origins to Destinations WITH separated routes
                        for gjs in gjsList:
                            from_poi_id = gjs['features'][0]['properties']['From']
                            to_poi_id = gjs['features'][0]['properties']['To'] 
                            outName = path + "/{0}_to_{1}_by_{2}.json".format(from_poi_id, to_poi_id, PROFILE ) 
                            write2File(outName, gjs)
                            fileList.append(outName)

                    else:                                                 # Origins to Destinations NO separated routes     
                        #map responses into one geojson
                        gjs = { "type": 'FeatureCollection',  "features": []}
                        for item in  gjsList: 
                            gjs['features'] += item['features']

                        #Write output
                        outName =  path + "/Routings_{0}_{1}.json".format(PROFILE.upper(), time_now() ) 
                        write2File(outName , gjs )
                        fileList = [outName]

                    # add to map
                    groupName = PROFILE.upper() + "_Routings"
                    addGeojsonsToMap(self.iface, fileList, groupName, size, color )
