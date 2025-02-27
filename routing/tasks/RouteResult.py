from ...clients.publish_api.Models import RouteResponse

class RouteResult(object):
    def __init__(self, element: int, result: RouteResponse) -> None:
        self.result = result
        self.element = element