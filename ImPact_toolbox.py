import os.path

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import QAction, QDialog

from .settings import MESSAGE_CATEGORY
# Initialize Qt resources from file resources.py
# Import the code for the dialog
from .ImPact_toolbox_dialog import ToolBoxDialog
from .upload_dataset_dialog import UploadDatasetDialog
from .auth.DeviceFlowAuth import DeviceFlowAuth
from .clients.api.ApiClient import ApiClient
from .clients.api.ApiClientSettings import ApiClientSettings
from qgis.core import *
# The import 'from .resources import *' is needed to load the resources (e.g. the icon)
from .resources import *

class ToolBox:
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
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'ImPact_toolbox_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = '&ANYWAYS'

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

        self.auth = DeviceFlowAuth()
        self._project_cache = {"projects": None}

        self.profile_keys = [
			"car.fast",
			"car.fast.5%",
			"car.fast.10%",
			"car.short",
			"car.short.5%",
			"car.short.10%",
			"car.classifications",
			"car.classifications.5%",
			"car.classifications.10%",
			"bicycle.comfort_safety",
			"bicycle.comfort_safety.5%",
			"bicycle.comfort_safety.10%",
			"bicycle.comfort",
			"bicycle.comfort.5%",
			"bicycle.comfort.10%",
			"bicycle.commute",
			"bicycle.commute.5%",
			"bicycle.commute.10%",
			"bicycle.fast",
			"bicycle.fast.5%",
			"bicycle.fast.10%",
			"bicycle.safety",
			"bicycle.safety.5%",
			"bicycle.safety.10%",
			"bicycle.short",
			"bicycle.short.5%",
			"bicycle.short.10%",
			"bigtruck.fast",
			"bigtruck.fast.5%",
			"bigtruck.fast.10%",
			"bigtruck.short",
			"bigtruck.short.5%",
			"bigtruck.short.10%",
			"pedestrian.short",
			"pedestrian.short.5%",
			"pedestrian.short.10%",
			"pedestrian.slow_roads",
			"pedestrian.slow_roads.5%",
			"pedestrian.slow_roads.10%"
        ]

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
        icon_path = ':/plugins/anyways_impact_toolbox/icon.png'
        self.add_action(
            icon_path,
            text='Plugin',
            callback=self.open_dialog,
            parent=self.iface.mainWindow())

        # Add "Upload to ANYWAYS..." to the layer tree context menu for all vector layers.
        # The check for line geometry + count attribute is done in the triggered slot.
        self._upload_action = QAction("Upload to ANYWAYS...", self.iface.mainWindow())
        self._upload_action.triggered.connect(self._on_upload_to_anyways)
        self.iface.addCustomActionForLayerType(self._upload_action, "", QgsMapLayerType.VectorLayer, True)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu('Plugin',
                action)
            self.iface.removeToolBarIcon(action)

        self.iface.removeCustomActionForLayerType(self._upload_action)

    def _is_uploadable_layer(self, layer):
        return (layer is not None
                and isinstance(layer, QgsVectorLayer)
                and layer.geometryType() == QgsWkbTypes.LineGeometry
                and layer.fields().indexFromName("count") >= 0)

    def _on_upload_to_anyways(self):
        layer = self.iface.activeLayer()
        if not self._is_uploadable_layer(layer):
            return

        if not self.auth.is_logged_in:
            self.iface.messageBar().pushMessage(
                "ANYWAYS", "Please log in first via the ANYWAYS plugin dialog.",
                level=Qgis.Warning, duration=5)
            return

        project_id = QgsProject.instance().readEntry("anyways", "selected_project_id")[0]
        if not project_id:
            self.iface.messageBar().pushMessage(
                "ANYWAYS", "Please select a project first via the ANYWAYS plugin dialog.",
                level=Qgis.Warning, duration=5)
            return

        # Look up project name from cache, fetch if cache is empty
        project_name = None
        cached = self._project_cache.get("projects")
        if not cached:
            try:
                api = ApiClient(ApiClientSettings(), get_token=self.auth.get_access_token)
                api.get_projects(lambda projects: self._project_cache.update({"projects": projects}))
                cached = self._project_cache.get("projects")
            except Exception:
                pass
        if cached:
            for p in cached:
                if p.get("id") == project_id:
                    org = p.get("_organization_name", "")
                    n = p.get("name", "")
                    project_name = f"{org} / {n}" if org else n
                    break
        if not project_name:
            project_name = project_id

        has_profile_attr = layer.fields().indexFromName("profile") >= 0

        # Validate profiles in layer against known profile keys
        if has_profile_attr:
            invalid_profiles = set()
            for feature in layer.getFeatures():
                val = str(feature.attribute("profile") or "").strip()
                if val and val not in self.profile_keys:
                    invalid_profiles.add(val)
            if invalid_profiles:
                self.iface.messageBar().pushMessage(
                    "ANYWAYS",
                    f"Layer contains unknown profile(s): {', '.join(sorted(invalid_profiles))}",
                    level=Qgis.Critical, duration=10)
                return

        dialog = UploadDatasetDialog(layer.name(), project_name, self.profile_keys,
                                     show_profile_picker=not has_profile_attr,
                                     parent=self.iface.mainWindow())
        if dialog.exec_() != QDialog.Accepted:
            return

        name = dialog.get_name()
        description = dialog.get_description()
        default_profile = dialog.get_profile()

        locations, trips = self._extract_dataset_from_layer(layer, default_profile)
        if not trips:
            self.iface.messageBar().pushMessage(
                "ANYWAYS", "No valid trips found in the layer.",
                level=Qgis.Warning, duration=5)
            return

        api = ApiClient(ApiClientSettings(), get_token=self.auth.get_access_token)
        try:
            def on_upload_complete():
                self.iface.messageBar().pushMessage(
                    "ANYWAYS", f"Dataset '{name}' uploaded successfully with {len(trips)} trips.",
                    level=Qgis.Success, duration=5)

            api.upload_dataset(project_id, name, description, locations, trips, on_upload_complete)
            api.track("dataset.create", {"projectId": project_id})
        except Exception as e:
            self.iface.messageBar().pushMessage(
                "ANYWAYS", f"Upload failed: {e}",
                level=Qgis.Critical, duration=10)

    def _extract_dataset_from_layer(self, layer, default_profile: str):
        import uuid

        crs = layer.crs()
        target_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        transform = QgsCoordinateTransform(crs, target_crs, QgsProject.instance())

        locations = {}  # (lon, lat) -> {"id": ..., "longitude": ..., "latitude": ...}
        trips = []

        has_profile = layer.fields().indexFromName("profile") >= 0

        for feature in layer.getFeatures():
            geom = feature.geometry()
            if geom.isEmpty():
                continue

            geom_copy = QgsGeometry(geom)
            geom_copy.transform(transform)

            vertices = list(geom_copy.vertices())
            if len(vertices) < 2:
                continue

            origin_point = vertices[0]
            dest_point = vertices[-1]

            origin_key = (round(origin_point.x(), 5), round(origin_point.y(), 5))
            dest_key = (round(dest_point.x(), 5), round(dest_point.y(), 5))

            if origin_key not in locations:
                locations[origin_key] = {
                    "id": str(uuid.uuid4()),
                    "longitude": origin_key[0],
                    "latitude": origin_key[1]
                }
            if dest_key not in locations:
                locations[dest_key] = {
                    "id": str(uuid.uuid4()),
                    "longitude": dest_key[0],
                    "latitude": dest_key[1]
                }

            count = feature.attribute("count")
            try:
                count = int(count)
            except (ValueError, TypeError):
                count = 0

            if has_profile:
                profile = str(feature.attribute("profile") or "").strip()
            else:
                profile = default_profile

            trips.append({
                "origin": locations[origin_key]["id"],
                "destination": locations[dest_key]["id"],
                "count": count,
                "profile": profile
            })

        return list(locations.values()), trips

    def open_dialog(self):
        """Called when the menu item is clicked"""
        QgsMessageLog.logMessage("Initing dialog", MESSAGE_CATEGORY, level=Qgis.Info)
        self.dlg = ToolBoxDialog(self.iface, self.profile_keys, self.auth, project_cache=self._project_cache)

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
