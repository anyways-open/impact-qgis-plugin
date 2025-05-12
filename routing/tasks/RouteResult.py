from ...clients.publish_api.Models.RouteMatrixResponse import RouteMatrixResponse

class RouteResult(object):
    def __init__(self, element: int, result: RouteMatrixResponse=None, message: str=None) -> None:
        self.result = result
        self.message = message
        self.element = element

    def is_success(self):
        return self.result is not None