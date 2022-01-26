import json


class route_meta(object):
    """
    A wrapper around a list of geojson-features with some metadat
    """

    def __init__(self, features, fromCoor, toCoor, profile, source, fromImpact=False):
        self.features = features
        self.fromCoor = fromCoor
        self.toCoor = toCoor
        self.profile = profile
        self.source = source
        self.fromImpact = fromImpact

    def save_feature(self, path):
        filename = path + "/%s to %s by %s.json" % (self.fromCoor, self.toCoor, self.profile.upper())

        f = open(filename, "w+")
        f.write(json.dumps(self.features))
        f.close()
        return filename

    def as_geojson(self):
        return json.dumps({
            "type": "FeatureCollection",
            "features": self.features
        })

    def __str__(self):
        return "RouteMeta(" + self.fromCoor + " --> " + self.toCoor + ", " + str(len(self.features)) + ")"
