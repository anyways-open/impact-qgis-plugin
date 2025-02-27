from .MatrixElement import MatrixElement
from .MatrixLocation import MatrixLocation
from .MatrixOriginLocation import MatrixOriginLocation

class Matrix(object):
    def __init__(self, locations: list[MatrixLocation], elements: list[MatrixElement]) -> None:
        self.locations = locations
        self.elements = elements