from .ProfileModel import ProfileModel
from .ProfileParametersModel import ProfileParametersModel
from ....routing.Matrix import Matrix
import json

class RouteMatrixRequest(object):
    def __init__(self, profile: ProfileModel, origins: list[list[float]], destinations: list[list[float]]):
        self.profile = profile
        self.origins = origins
        self.destinations = destinations

    def to_json(self) -> str:
        return json.dumps({
            "profile": {
                "name": self.profile.name,
                "parameters": {
                    "maxIncrease": self.profile.parameters.max_increase,
                }
            },
            "origins": self.origins,
            "destinations": self.destinations,
        })

    @staticmethod
    def from_matrix_per_element(profile: str, matrix: Matrix, element: int) -> 'RouteMatrixRequest':
        element = matrix.elements[element]

        origins: list[list[float]] = []
        origin_location = matrix.locations[element.origin]
        origins.append([origin_location.location.x(), origin_location.location.y()])

        destinations: list[list[float]] = []
        destination_location = matrix.locations[element.destination]
        destinations.append([destination_location.location.x(), destination_location.location.y()])

        profile_model = ProfileModel.from_profile_string(profile)

        return RouteMatrixRequest(profile_model, origins, destinations)

    @staticmethod
    def from_matrix_per_origin(profile: str, matrix: Matrix, origin: int) -> 'RouteMatrixRequest':
        # build origin list, a single origin.
        origins: list[list[float]] = []
        origin_location = matrix.locations[origin]
        origins.append([origin_location.location.x(), origin_location.location.y()])

        # build destination list, a single origin.
        destinations: list[list[float]] = []
        for element in matrix.elements:
            if element.origin != origin:
                continue
            destination_location = matrix.locations[element.destination]
            destinations.append([destination_location.location.x(), destination_location.location.y()])

        profile_model = ProfileModel.from_profile_string(profile)

        return RouteMatrixRequest(profile_model, origins, destinations)