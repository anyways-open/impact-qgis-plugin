from qgis._core import QgsPointXY

from .MatrixLocation import MatrixLocation

class MatrixOriginLocation(MatrixLocation):
    def __init__(self, location: QgsPointXY, count: int):
        super().__init__(location)
        self.count = count