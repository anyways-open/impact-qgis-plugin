from typing import Optional

from .....clients.publish_api.Models.Compact.CompactRouteSegment import CompactRouteSegment

class CompactRoute(object):
    def __init__(self, segments: list[CompactRouteSegment], error: Optional[str]):
        self.segments = segments
        self.error = error

    def is_error(self):
        return self.error is not None

    @staticmethod
    def from_json(response_json: dict) -> 'CompactRoute':
        if "error" in response_json:
            return CompactRoute([], response_json["error"])

        segments: list[CompactRouteSegment] = []
        json_segments: list = response_json["segments"]
        for json_segment in json_segments:
            segments.append(CompactRouteSegment.from_json(json_segment))

        return CompactRoute(segments, None)