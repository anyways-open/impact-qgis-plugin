from .NetworkModel import NetworkModel
from .ResponseModel import ResponseModel
from .ScenarioModel import ScenarioModel

class ProjectModel(object):
    def __init__(self, global_id: str, name: str, networks: list[str], scenarios: list[str]) -> None:
        self.global_id = global_id
        self.name = name
        self.networks = networks
        self.scenarios = scenarios

    @staticmethod
    def from_response_json(response_json) -> 'ResponseModel[ProjectModel]':
        name: str = response_json["details"]["name"]
        global_id: str = response_json["details"]["id"]
        network_ids: list = response_json["details"]["networks"]
        scenario_ids: list = response_json["details"]["scenarios"]

        scenarios: dict[str, ScenarioModel] = dict()
        for json_scenario in response_json["scenarios"]:
            scenario = ScenarioModel.from_json(json_scenario)
            scenarios[scenario.global_id] = scenario

        networks: dict[str, NetworkModel] = dict()
        for json_network in response_json["networks"]:
            network = NetworkModel.from_json(json_network)
            networks[network.global_id] = network

        project = ProjectModel(global_id, name, network_ids, scenario_ids)

        return ResponseModel(project, networks, scenarios)