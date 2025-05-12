from ....clients.publish_api.Models.RouteModel import RouteModel
from ....geojson.GeoJsonFeature import GeoJsonFeature

class RouteMatrixResponse(object):
    def __init__(self, segments: dict[str, GeoJsonFeature], routes: list[list[list[RouteModel]]]):
        self.segments = segments
        self.routes = routes

    @staticmethod
    def from_json(response_json: dict) -> 'RouteMatrixResponse':
        # parse segments as features.
        segments: dict[str, GeoJsonFeature] = {}
        json_segments: dict = response_json["segments"]
        for key, value in json_segments.items():
            segments[key] = RouteMatrixResponse.feature_from_segment_json(value)

        # parse the routes
        json_route_rows = response_json["routes"]
        routes: list[list[list[RouteModel]]] = []
        for json_route_row in json_route_rows:
            route_row: list[list[RouteModel]] = []
            routes.append(route_row)
            for json_alternative_routes in json_route_row:
                alternatives: list[RouteModel] = []
                route_row.append(alternatives)
                for json_alternative in json_alternative_routes:
                    alternatives.append(RouteModel.from_json(json_alternative))

        return RouteMatrixResponse(segments, routes)

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