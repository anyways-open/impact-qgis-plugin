from qgis._core import QgsMessageLog, Qgis, QgsVectorLayer
from ..clients.publish_api.Models.RouteResponse import RouteResponse
from ..Result import Result
from ..settings import MESSAGE_CATEGORY
import json

class HistogramLayerBuilder(object):
    def __init__(self, name: str, results: list[Result[RouteResponse]]):
        self.name = name
        self.results = results

    def build_layer(self, filename: str) -> QgsVectorLayer:
        # QgsMessageLog.logMessage(f"Results in layer: {self.results}", MESSAGE_CATEGORY, Qgis.Info)

        # extract all segments.
        flattened = list()
        for result in self.results:
            # QgsMessageLog.logMessage(f"Result in layer: {result}", MESSAGE_CATEGORY, Qgis.Info)
            if result.result is None:
                # todo: error layer
                continue

            for segment in result.result.feature["features"]:
                flattened.append(segment)

        # QgsMessageLog.logMessage(f"{flattened}", MESSAGE_CATEGORY, Qgis.Info)

        histogram: dict[str, object] = dict()
        for result in flattened:
            if result["type"] is None:
                raise Exception("Result is not a feature")

            if result["type"] == "LineString":
                continue

            if "properties" not in result:
                continue
            properties = result["properties"]
            if properties is None:
                continue

            if "_segment_guid" not in properties or properties["_segment_guid"] is None:
                continue
            segment_guid = properties["_segment_guid"]

            if "_segment_forward" not in properties or properties["_segment_forward"] is None:
                continue
            segment_forward = properties["_segment_forward"]

            count = 1
            if 'count' in properties:
                count = properties["count"]

            if segment_guid in histogram:
                histogram[segment_guid]["properties"]["count"] += count
            else:
                properties["count"] = count
                histogram[segment_guid] = result

            QgsMessageLog.logMessage(f"{segment_guid}{segment_forward}: {result}", MESSAGE_CATEGORY, Qgis.Info)

        f = open(filename, "w+")
        f.write(json.dumps({
            "type": 'FeatureCollection',
            "features": list(histogram.values())
        }))
        f.close()

        return QgsVectorLayer(filename, self.name, "ogr")
