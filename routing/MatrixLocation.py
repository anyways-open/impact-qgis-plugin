from qgis._core import QgsPointXY

class MatrixLocation(object):
    def __init__(self, location: QgsPointXY):
        self.location = location