class ScenarioModel(object):
    def __init__(self, global_id: str, name: str, network: str) -> None:
        self.global_id = global_id
        self.name = name
        self.network = network

    @staticmethod
    def from_json(json) -> 'ScenarioModel':
        global_id = json["id"]
        name = json["name"]
        network = json["network"]

        return ScenarioModel(global_id, name, network)