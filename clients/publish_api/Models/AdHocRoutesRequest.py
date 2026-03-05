from ....routing.Matrix import Matrix
import json

class AdHocRoutesRequest(object):
    def __init__(self, locations: list[dict], trips: list[dict]):
        self.locations = locations
        self.trips = trips

    def to_json(self) -> str:
        return json.dumps({
            "locations": self.locations,
            "trips": self.trips,
        })

    @staticmethod
    def from_matrix(profile: str, matrix: Matrix) -> 'AdHocRoutesRequest':
        # build locations list from all unique matrix locations
        locations: list[dict] = []
        for loc in matrix.locations:
            locations.append({
                "longitude": loc.location.x(),
                "latitude": loc.location.y()
            })

        # build trips from all matrix elements
        trips: list[dict] = []
        for element in matrix.elements:
            trips.append({
                "origin": element.origin,
                "destination": element.destination,
                "count": element.count,
                "profile": profile
            })

        return AdHocRoutesRequest(locations, trips)
