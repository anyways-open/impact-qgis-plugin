from typing import Optional

from ....clients.publish_api.Models.RouteSegmentModel import RouteSegmentModel

class RouteModel(object):
    def __init__(self, segments: list[RouteSegmentModel], error: Optional[str]):
        self.segments = segments
        self.error = error

    def is_error(self):
        return self.error is not None

    @staticmethod
    def from_json(response_json: dict) -> 'RouteModel':
        if "error" in response_json:
            return RouteModel([], response_json["error"])

        segments: list[RouteSegmentModel] = []
        json_segments: list = response_json["segments"]
        for json_segment in json_segments:
            segments.append(RouteSegmentModel.from_json(json_segment))

        return RouteModel(segments, None)