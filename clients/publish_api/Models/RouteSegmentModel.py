class RouteSegmentModel(object):
    def __init__(self, segment_id: str, forward: bool):
        self.segment_id = segment_id
        self.forward = forward

    @staticmethod
    def from_json(response_json: dict) -> 'RouteSegmentModel':
        segment_id: str = response_json["segment"]
        forward: bool = response_json["forward"]

        return RouteSegmentModel(segment_id, forward)
