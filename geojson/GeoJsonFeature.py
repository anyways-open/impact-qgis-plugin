import copy
import math
from typing import Union, Any

from qgis._core import QgsMessageLog, Qgis

from ..settings import MESSAGE_CATEGORY


class GeoJsonFeature(object):
    def __init__(self, feature: dict):
        self.feature = feature

    @staticmethod
    def to_feature_collection(features: list['GeoJsonFeature']) -> dict[str, Union[str, list[Any]]]:
        raw_features = []
        for feature in features:
            raw_features.append(feature.feature)

        return {
            "type": 'FeatureCollection',
            "features": raw_features
        }

    @staticmethod
    def reverse_linestring(feature: 'GeoJsonFeature') -> 'GeoJsonFeature':
        coordinates: list[list[float]] = feature.feature["geometry"]["coordinates"]
        reversed_coordinates: list[list[float]] = list(reversed(coordinates))

        properties = copy.deepcopy(feature.feature["properties"])
        properties["_reversed"] = True

        return GeoJsonFeature({
            "type": "Feature",
            "properties": properties,
            "geometry": {
                "type": "LineString",
                "coordinates": reversed_coordinates
            }
        })

    def get_length(self):
        length = 0.0
        coordinates: list[list[float]] = self.feature["geometry"]["coordinates"]

        for c in range(1, len(coordinates)):
            length += math.sqrt (math.pow(coordinates[c-1][0] - coordinates[c][0], 2) + math.pow(coordinates[c-1][1] - coordinates[c][1], 2))

        return length

    def get_cut(self, tail_offset: int, head_offset: int) -> 'GeoJsonFeature':
        length = self.get_length()

        tail = length * (tail_offset / 65535.0)
        head = length * (head_offset / 65535.0)
        QgsMessageLog.logMessage(f"{length} - {tail} - {head}", MESSAGE_CATEGORY, Qgis.Info)

        if tail > head:
            raise ValueError("tail offset is greater than head offset")

        coordinates: list[list[float]] = self.feature["geometry"]["coordinates"]
        cut_coordinates: list[list[float]] = []

        current = 0.0
        for c in range(1, len(coordinates)):
            x_diff = coordinates[c - 1][0] - coordinates[c][0]
            y_diff = coordinates[c - 1][1] - coordinates[c][1]
            segment_length = math.sqrt(math.pow(x_diff, 2) + math.pow(y_diff, 2))
            if segment_length <= 0:
                continue

            n = current + segment_length
            QgsMessageLog.logMessage(f"STEP {c}/{len(coordinates)}@{len(cut_coordinates)} - {current} - {segment_length}", MESSAGE_CATEGORY, Qgis.Info)

            if len(cut_coordinates) <= 0:
                if n >= tail:
                    if tail <= 0:
                        cut_coordinates.append(coordinates[c-1])
                    else:
                        tail_segment_offset = (n - tail) / segment_length
                        if tail_segment_offset <= 0:
                            cut_coordinates.append(coordinates[c-1])
                        else:
                            interpolated = [coordinates[c][0] + (x_diff * tail_segment_offset),coordinates[c][1] + (y_diff * tail_segment_offset)]
                            cut_coordinates.append(interpolated)
                    QgsMessageLog.logMessage(f"STEP {c}/{len(coordinates)}@{len(cut_coordinates)} - TAIL FOUND", MESSAGE_CATEGORY, Qgis.Info)

            if len(cut_coordinates) > 0:
                if n <= head:
                    cut_coordinates.append(coordinates[c])
                    QgsMessageLog.logMessage(f"STEP {c}/{len(coordinates)}@{len(cut_coordinates)} - INCLUDED", MESSAGE_CATEGORY, Qgis.Info)
                if n == head:
                    QgsMessageLog.logMessage(f"STEP {c}/{len(coordinates)}@{len(cut_coordinates)} - EXACT HEAD FOUND", MESSAGE_CATEGORY, Qgis.Info)
                    break
                if n > head:
                    head_segment_offset = (n - head) / segment_length
                    interpolated = [coordinates[c][0] + (x_diff * head_segment_offset),coordinates[c][1] + (y_diff * head_segment_offset)]
                    cut_coordinates.append(interpolated)
                    QgsMessageLog.logMessage(f"STEP {c}/{len(coordinates)}@{len(cut_coordinates)} - HEAD FOUND", MESSAGE_CATEGORY, Qgis.Info)
                    break

            current = n

        properties = copy.deepcopy(self.feature["properties"])

        if len(cut_coordinates) <= 1:
            raise ValueError("cut is empty or only has one coordinate")

        return GeoJsonFeature({
            "type": "Feature",
            "properties": properties,
            "geometry": {
                "type": "LineString",
                "coordinates": cut_coordinates
            }
        })

    def append_coordinates(self, coordinates: list[list[float]], reverse: bool = False) -> None:
        self_coordinates: list[list[float]] = self.feature["geometry"]["coordinates"]

        if reverse:
            for coordinate in reversed(self_coordinates):
                coordinates.append(coordinate)
            return

        for coordinate in self_coordinates:
            coordinates.append(coordinate)
        return

    def get_properties(self) -> dict:
        if "properties" not in self.feature:
            self.feature["properties"] = {}
        if self.feature["properties"] is None:
            self.feature["properties"] = {}
        return self.feature["properties"]

    def add_to_attribute_value(self, key, increment: float):
        properties = self.get_properties()

        value = 0
        if key in properties:
            value: float = properties[key]

        value += increment
        properties[key] = value

    def add_or_update_attribute(self, key: str, value: str):
        properties = self.get_properties()

        properties[key] = value

    def round_attribute_value(self, key):
        properties = self.get_properties()

        if not key in properties:
            return

        value: float = properties[key]
        properties[key] = round(value, 2)
