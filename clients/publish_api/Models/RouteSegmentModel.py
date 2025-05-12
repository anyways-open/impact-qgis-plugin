class RouteSegmentModel(object):
    def __init__(self, global_id: str, forward: bool, tail_offset: int, head_offset: int, time: float):
        self.global_id = global_id
        self.forward = forward
        self.tail_offset = tail_offset
        self.head_offset = head_offset
        self.time = time

    @staticmethod
    def from_json(response_json: dict) -> 'RouteSegmentModel':
        global_id: str = response_json["id"]
        forward: bool = response_json["forward"]
        tail_offset: int = 0
        if "tailOffset" in response_json:
            tail_offset: int = response_json["tailOffset"]
        head_offset: int = 65535
        if "headOffset" in response_json:
            head_offset: int = response_json["headOffset"]
        time: float = response_json["time"]

        return RouteSegmentModel(global_id, forward, tail_offset, head_offset, time)
