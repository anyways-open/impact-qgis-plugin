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

    def build_layer(self, project_path: str) -> QgsVectorLayer:
        cuts_per_segment: dict[str, list[int]] = dict()
        for i, result in enumerate(self.results):
            if not result.is_success():
                continue

            response = result.result
            for route_row in response.routes:
                for alternatives in route_row:
                    for route in alternatives:
                        for route_segment in route.segments:
                            segment_key = f'{route_segment.global_id}-{route_segment.forward}'
                            segment_cuts: list[int] = []
                            if segment_key in cuts_per_segment:
                                segment_cuts = cuts_per_segment[segment_key]

                            if route_segment.tail_offset not in segment_cuts:
                                segment_cuts.append(route_segment.tail_offset)
                                segment_cuts = sorted(segment_cuts)
                            if route_segment.head_offset not in segment_cuts:
                                segment_cuts.append(route_segment.head_offset)
                                segment_cuts = sorted(segment_cuts)

                            cuts_per_segment[segment_key] = segment_cuts

        # QgsMessageLog.logMessage(f"{flattened}", MESSAGE_CATEGORY, Qgis.Info)
        histogram: dict[str, GeoJsonFeature] = dict()
        for i, result in enumerate(self.results):
            if not result.is_success():
                continue

            element = self.matrix.elements[i]

            response = result.result
            for route_row in response.routes:
                for alternatives in route_row:
                    count_per_alternative = (element.count + 0.0) / len(alternatives)
                    for route in alternatives:
                        for route_segment in route.segments:
                            segment_key = f'{route_segment.global_id}-{route_segment.forward}'

                            # get the cuts covered by this route_segment
                            segment_cuts = cuts_per_segment[segment_key]
                            covered_cuts: list[int] = []
                            for segment_cut in segment_cuts:
                                if route_segment.tail_offset > segment_cut:
                                    continue
                                if route_segment.head_offset < segment_cut:
                                    continue

                                covered_cuts.append(segment_cut)

                            # process the segment for each cut
                            for k in range(1, len(covered_cuts)):
                                tail_offset = covered_cuts[k - 1]
                                head_offset = covered_cuts[k]
                                segment_cut_key = f'{route_segment.global_id}-{route_segment.forward}@{tail_offset}-{head_offset}'

                                if segment_cut_key not in histogram:
                                    segment = response.segments[route_segment.global_id]
                                    if segment is None:
                                        raise RuntimeError(f"Invalid response: could not find segment {route_segment.global_id}")

                                    if not route_segment.forward:
                                        segment = GeoJsonFeature.reverse_linestring(segment)

                                    if tail_offset != 0 or head_offset != 65535:
                                        QgsMessageLog.logMessage(f"{segment_cut_key}", MESSAGE_CATEGORY, Qgis.Info)
                                        QgsMessageLog.logMessage(f"{segment}", MESSAGE_CATEGORY, Qgis.Info)
                                        segment = segment.get_cut(tail_offset, head_offset)

                                    histogram[segment_cut_key] = segment
                                else:
                                     segment = histogram[segment_cut_key]

                                segment.add_to_attribute_value("count", count_per_alternative)
                                segment.add_or_update_attribute("id", segment_cut_key)

            #QgsMessageLog.logMessage(f"{segment_guid}{segment_forward}: {result}", MESSAGE_CATEGORY, Qgis.Info)

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
