class DatasetLocationModel(object):
    def __init__(self, global_id: str, longitude: float, latitude: float) -> None:
        self.global_id = global_id
        self.longitude = longitude
        self.latitude = latitude

    @staticmethod
    def from_json(json) -> 'DatasetLocationModel':
        global_id = json["id"]
        longitude = json.get("longitude", 0)
        latitude = json.get("latitude", 0)
        return DatasetLocationModel(global_id, longitude, latitude)


class DatasetTripModel(object):
    def __init__(self, origin: str, destination: str, count: int, profile: str) -> None:
        self.origin = origin
        self.destination = destination
        self.count = count
        self.profile = profile

    @staticmethod
    def from_json(json) -> 'DatasetTripModel':
        origin = json.get("origin", "")
        destination = json.get("destination", "")
        count = json.get("count", 0)
        profile = json.get("profile", "")
        return DatasetTripModel(origin, destination, count, profile)


class DatasetModel(object):
    def __init__(self, global_id: str, name: str, description: str, last_modified: str) -> None:
        self.global_id = global_id
        self.name = name
        self.description = description
        self.last_modified = last_modified

    @staticmethod
    def from_json(json) -> 'DatasetModel':
        global_id = json["id"]
        name = json.get("name", global_id)
        description = json.get("description", "")
        last_modified = json.get("lastModified", "")
        return DatasetModel(global_id, name, description, last_modified)
