from ...clients.publish_api.Models.Compact.MatrixCompactResponse import MatrixCompactResponse

class RouteResult(object):
    def __init__(self, element: int, result: MatrixCompactResponse=None, message: str=None) -> None:
        self.result = result
        self.message = message
        self.element = element

    def is_success(self):
        return self.result is not None