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

    def get_properties(self) -> dict:
        if "properties" not in self.feature:
            self.feature["properties"] = {}
        if self.feature["properties"] is None:
            self.feature["properties"] = {}
        return self.feature["properties"]

    def add_to_attribute_value(self, key, increment):
        properties = self.get_properties()

        value = 0
        if key in properties:
            value: int = properties["count"]

        value += increment
        properties[key] = value
