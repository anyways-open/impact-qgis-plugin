from PyQt5.QtCore import QVariant

from .....geojson.GeoJsonFeature import GeoJsonFeature
from .....clients.publish_api.Models.Compact.CompactRoute import CompactRoute

class MatrixCompactResponse(object):
    def __init__(self, segments: dict[str, GeoJsonFeature], routes: list[list[CompactRoute]]):
        self.segments = segments
        self.routes = routes

    @staticmethod
    def from_json(response_json: dict) -> 'MatrixCompactResponse':
        # parse segments as features.
        segments: dict[str, GeoJsonFeature] = {}
        json_segments: dict = response_json["segments"]
        for key, value in json_segments.items():
            segments[key] = MatrixCompactResponse.feature_from_segment_json(value)

        # parse the routes
        json_route_rows = response_json["routes"]
        routes: list[list[CompactRoute]] = []
        for json_route_row in json_route_rows:
            route_row: list[CompactRoute] = []
            routes.append(route_row)
            for json_route in json_route_row:
                route_row.append(CompactRoute.from_json(json_route))

        return MatrixCompactResponse(segments, routes)

    @staticmethod
    def feature_from_segment_json(response_json: dict) -> GeoJsonFeature:
        return GeoJsonFeature({
            "type": 'Feature',
            "properties": response_json["attributes"],
            "geometry": {
                "type": "LineString",
                "coordinates": response_json["shape"],
            }
        })