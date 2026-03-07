from ...clients.publish_api.Models.AdHocRoutesResponse import AdHocRoutesResponse

class RouteResult(object):
    def __init__(self, result: AdHocRoutesResponse=None, message: str=None) -> None:
        self.result = result
        self.message = message

    def is_success(self):
        return self.result is not None
