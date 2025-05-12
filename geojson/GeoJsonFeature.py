import copy


class GeoJsonFeature(object):
    def __init__(self, feature: dict):
        self.feature = feature

    @staticmethod
    def to_feature_collection(features: list['GeoJsonFeature']) -> []:
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
