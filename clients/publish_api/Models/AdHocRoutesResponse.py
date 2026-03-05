from typing import Optional

from ....clients.publish_api.Models.RouteModel import RouteModel
from ....geojson.GeoJsonFeature import GeoJsonFeature

class AdHocRoutesResponse(object):
    def __init__(self, segments: dict[str, GeoJsonFeature], routes: list[RouteModel], batch: Optional[str]):
        self.segments = segments
        self.routes = routes
        self.batch = batch

    def merge(self, other: 'AdHocRoutesResponse') -> 'AdHocRoutesResponse':
        merged_segments = dict(self.segments)
        merged_segments.update(other.segments)
        merged_routes = list(self.routes) + list(other.routes)
        return AdHocRoutesResponse(merged_segments, merged_routes, other.batch)

    @staticmethod
    def from_json(response_json: dict) -> 'AdHocRoutesResponse':
        # parse segments as features (v3: array of {id, geometry, attributes})
        segments: dict[str, GeoJsonFeature] = {}
        for segment_obj in response_json.get("segments", []):
            segment_id = segment_obj["id"]
            segments[segment_id] = GeoJsonFeature({
                "type": "Feature",
                "properties": segment_obj.get("attributes", {}),
                "geometry": segment_obj["geometry"]
            })

        # parse routes (v3: flat array)
        routes: list[RouteModel] = []
        for json_route in response_json.get("routes", []):
            routes.append(RouteModel.from_json(json_route))

        batch = response_json.get("batch", None)

        return AdHocRoutesResponse(segments, routes, batch)
