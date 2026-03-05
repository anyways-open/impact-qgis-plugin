# -*- coding: utf-8 -*-

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load ToolBox class from file ToolBox.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from qgis.core import QgsMessageLog, Qgis
    QgsMessageLog.logMessage("ImPact plugin loaded — v3 API (2026-03-05-b)", "ANYWAYS", Qgis.Info)

    from .ImPact_toolbox import ToolBox
    return ToolBox(iface)
