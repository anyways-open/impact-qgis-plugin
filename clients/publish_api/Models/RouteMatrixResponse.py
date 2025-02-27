from qgis._core import QgsMessageLog, Qgis

from ....settings import MESSAGE_CATEGORY
from ....clients.publish_api.Models.RouteResponse import RouteResponse

class RouteMatrixResponse(object):
    def __init__(self, routes: list[list[RouteResponse]]):
        self.routes = routes

    @staticmethod
    def from_json(response_json: dict) -> 'RouteMatrixResponse':
        routes = response_json["routes"]

        route_responses: list[list[RouteResponse]] = []
        for routes_for_origin in routes:
            route_response_for_origin: list[RouteResponse] = []

            for route_for_origin in routes_for_origin:
                route_response_for_origin.append(RouteResponse(route_for_origin))

            route_responses.append(route_response_for_origin)

        return RouteMatrixResponse(route_responses)