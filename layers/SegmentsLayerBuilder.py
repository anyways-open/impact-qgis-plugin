from qgis._core import QgsVectorLayer, QgsMessageLog, Qgis

from ..settings import MESSAGE_CATEGORY
from ..geojson.GeoJsonFeature import GeoJsonFeature
from ..routing.tasks.RouteResult import RouteResult
from ..routing.Matrix import Matrix
import json

class SegmentsLayerBuilder(object):
    def __init__(self, layer_name: str, matrix: Matrix,  results: list[RouteResult]):
        self.layer_name = layer_name
        self.matrix = matrix
        self.results = results

    @staticmethod
    def _get_segment_offsets(alternative, seg_idx: int, num_segments: int) -> tuple[int, int]:
        """Get tail/head offsets for a segment based on its position in the alternative.
        Returns offsets in 0-65535 range for compatibility with get_cut()."""
        if num_segments == 1:
            tail = alternative.tail
            head = alternative.head
        elif seg_idx == 0:
            tail = alternative.tail
            head = 100
        elif seg_idx == num_segments - 1:
            tail = 0
            head = alternative.head
        else:
            tail = 0
            head = 100

        # convert 0-100 percentage to 0-65535 range
        tail_65535 = int(tail * 65535 / 100)
        head_65535 = int(head * 65535 / 100)
        return tail_65535, head_65535

    def build_layer(self, project_path: str) -> QgsVectorLayer:
        # first pass: collect all segment cuts across all routes
        cuts_per_segment: dict[str, list[int]] = dict()
        for result in self.results:
            if not result.is_success():
                continue

            response = result.result
            for route in response.routes:
                if route.is_error():
                    continue
                for alternative in route.alternatives:
                    num_segments = len(alternative.segments)
                    for seg_idx, route_segment in enumerate(alternative.segments):
                        segment_key = f'{route_segment.segment_id}-{route_segment.forward}'
                        segment_cuts: list[int] = cuts_per_segment.get(segment_key, [])

                        tail_offset, head_offset = self._get_segment_offsets(alternative, seg_idx, num_segments)

                        if tail_offset not in segment_cuts:
                            segment_cuts.append(tail_offset)
                            segment_cuts = sorted(segment_cuts)
                        if head_offset not in segment_cuts:
                            segment_cuts.append(head_offset)
                            segment_cuts = sorted(segment_cuts)

                        cuts_per_segment[segment_key] = segment_cuts

        # second pass: build histogram of segment usage
        histogram: dict[str, GeoJsonFeature] = dict()
        for result in self.results:
            if not result.is_success():
                continue

            response = result.result
            for route_idx, route in enumerate(response.routes):
                if route.is_error():
                    continue

                # routes correspond 1:1 to matrix elements (trips sent in same order)
                element = self.matrix.elements[route_idx]

                num_alternatives = max(len(route.alternatives), 1)
                count_per_alternative = (element.count + 0.0) / num_alternatives

                for alternative in route.alternatives:
                    num_segments = len(alternative.segments)
                    for seg_idx, route_segment in enumerate(alternative.segments):
                        segment_key = f'{route_segment.segment_id}-{route_segment.forward}'
                        tail_offset, head_offset = self._get_segment_offsets(alternative, seg_idx, num_segments)

                        # get the cuts covered by this route_segment
                        segment_cuts = cuts_per_segment[segment_key]
                        covered_cuts: list[int] = []
                        for segment_cut in segment_cuts:
                            if tail_offset > segment_cut:
                                continue
                            if head_offset < segment_cut:
                                continue
                            covered_cuts.append(segment_cut)

                        # process the segment for each cut
                        for k in range(1, len(covered_cuts)):
                            cut_tail = covered_cuts[k - 1]
                            cut_head = covered_cuts[k]
                            segment_cut_key = f'{route_segment.segment_id}-{route_segment.forward}@{cut_tail}-{cut_head}'

                            if segment_cut_key not in histogram:
                                segment = response.segments.get(route_segment.segment_id)
                                if segment is None:
                                    raise RuntimeError(f"Invalid response: could not find segment {route_segment.segment_id}")

                                if not route_segment.forward:
                                    segment = GeoJsonFeature.reverse_linestring(segment)

                                if cut_tail != 0 or cut_head != 65535:
                                    segment = segment.get_cut(cut_tail, cut_head)
                                    if segment is None:
                                        continue

                                histogram[segment_cut_key] = segment
                            else:
                                 segment = histogram[segment_cut_key]

                            segment.add_to_attribute_value("count", count_per_alternative)
                            segment.add_or_update_attribute("id", segment_cut_key)

        # round numbers to format properly.
        for result in histogram.values():
            result.round_attribute_value("count")

        # write layer data as geojson
        result_layer_filename = f"{project_path}/{self.layer_name}.geojson"
        f = open(result_layer_filename, "w+")
        f.write(json.dumps(GeoJsonFeature.to_feature_collection(list(histogram.values()))))
        f.close()

        # create vector layer from geojson file.
        result_layer = QgsVectorLayer(result_layer_filename, self.layer_name, "ogr")

        return result_layer
