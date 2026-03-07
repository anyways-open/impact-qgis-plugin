from typing import Optional

from ....clients.publish_api.Models.RouteSegmentModel import RouteSegmentModel

class RouteAlternative(object):
    def __init__(self, segments: list[RouteSegmentModel], tail: int, head: int):
        self.segments = segments
        self.tail = tail
        self.head = head

    @staticmethod
    def from_json(response_json: dict) -> 'RouteAlternative':
        segments: list[RouteSegmentModel] = []
        for json_segment in response_json.get("segments", []):
            segments.append(RouteSegmentModel.from_json(json_segment))
        tail = response_json.get("tail", 0)
        head = response_json.get("head", 100)
        return RouteAlternative(segments, tail, head)

class RouteModel(object):
    def __init__(self, origin: str, destination: str, profile: str,
                 alternatives: list[RouteAlternative], is_error: Optional[str]):
        self.origin = origin
        self.destination = destination
        self.profile = profile
        self.alternatives = alternatives
        self.error = is_error

    def is_error(self):
        return self.error is not None

    @staticmethod
    def from_json(response_json: dict) -> 'RouteModel':
        origin = response_json.get("origin", "")
        destination = response_json.get("destination", "")
        profile = response_json.get("profile", "")
        is_error = response_json.get("isError", None)

        alternatives: list[RouteAlternative] = []
        for json_alt in response_json.get("alternatives", []):
            alternatives.append(RouteAlternative.from_json(json_alt))

        return RouteModel(origin, destination, profile, alternatives, is_error)
