import json
from qgis.PyQt import *
from qgis.PyQt.QtGui import *

from . import features_as_geojson_features, fetch_non_blocking


class fod_api(object):

    def __init__(self):
        pass

    def merge_modes(self, features, allowedModes):
        """
        Given the featurecollection of the call, will merge identical lines together and sum their totals
        :param features: a featurecollection
        :param allowedModes: a set of allowed modes
        :return: A list of features
        """

        fromApiDict = {}  # type: { fromId --> { toId --> geojsonfeature }}
        allFeatures = []
        for f in features:
            props = f["properties"]
            fromId = props["from_location"]
            toId = props["to_location"]
            count = props["count"]
            mode = props["mode"]
            if mode not in allowedModes:
                continue
            if fromId not in fromApiDict:
                fromApiDict[fromId] = {}
            toApiDict = fromApiDict[fromId]
            if toId not in toApiDict:
                toApiDict[toId] = f
                allFeatures.append(f)
            else:
                toApiDict[toId]["properties"]["count"] = toApiDict[toId]["properties"]["count"] + count
                toApiDict[toId]["properties"]["mode"] = toApiDict[toId]["properties"]["mode"] + ";" + mode
        return allFeatures

    def request(self, from_features, to_features, withPairs, onError, modes=None):
        """
        Requests all movement pairs between a from-location and a to-location from the FOD-API.
        
        :param from_features: either a QGIS-Layer or a geojson
        :param to_features: either a QGIS-Layer or a geojson
        :param modes: a list of applicable nodes. Supported are: "Bicycle", "Car", "BusOrTram", "Train". Note: they use uppercase! Using wrong modes will result in an empty result; using None will not filter
        :return: 
        """

        if (len(modes) == 0):
            print("Invalid: no modes given when requesting an FOD-response. Ignoring mode filter")
            modes = None

        if isinstance(from_features, str):
            from_features = json.loads(from_features)
        else:
            from_features = {"type": "FeatureCollection",
                             "features": features_as_geojson_features(from_features)}

        if isinstance(to_features, str):
            to_features = json.loads(to_features)
        else:
            to_features = {
                "type": "FeatureCollection",
                "features": features_as_geojson_features(to_features)
            }

        request_data = {"fromArea": from_features,
                        "toArea": to_features}

        head = {'Content-type': 'application/json-patch+json', 'Accept': 'application/geo+json'}
        
        def withData(raw):
            data = json.loads(raw)
            if (modes is not None):
                data["features"] = self.merge_modes(data["features"], modes)
            withPairs(data)

        headers = {'Content-Type': 'application/json-patch+json', 'Accept': 'application/geo+json'}
        fetch_non_blocking('https://api.anyways.eu/data/od/movement/area', withData, onError, postData=request_data,
                           headers=headers)
