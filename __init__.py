# -*- coding: utf-8 -*-

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load ToolBox class from file ToolBox.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .ImPact_toolbox import ToolBox
    return ToolBox(iface)
