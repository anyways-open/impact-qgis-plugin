class NetworkModel(object):
    def __init__(self, global_id: str, name: str, branch: str) -> None:
        self.global_id = global_id
        self.name = name
        self.branch = branch

    @staticmethod
    def from_json(json) -> 'NetworkModel':
        global_id = json["id"]
        name = json["name"]
        branch = json["branch"]

        return NetworkModel(global_id, name, branch)