from .DatasetModel import DatasetModel
from .NetworkModel import NetworkModel
from .ResponseModel import ResponseModel
from .ScenarioModel import ScenarioModel

class ProjectModel(object):
    def __init__(self, global_id: str, name: str, networks: list[str], scenarios: list[str], datasets: list[str]) -> None:
        self.global_id = global_id
        self.name = name
        self.networks = networks
        self.scenarios = scenarios
        self.datasets = datasets

    @staticmethod
    def from_response_json(data: list) -> 'ResponseModel[ProjectModel]':
        # v3 returns a flat array of DataObjects, filter by _type
        project_obj = None
        networks: dict[str, NetworkModel] = dict()
        scenarios: dict[str, ScenarioModel] = dict()
        datasets: dict[str, DatasetModel] = dict()

        for item in data:
            item_type = item.get("_type", "")
            if item_type == "project":
                project_obj = item
            elif item_type == "network":
                network = NetworkModel.from_json(item)
                networks[network.global_id] = network
            elif item_type == "scenario":
                scenario = ScenarioModel.from_json(item)
                scenarios[scenario.global_id] = scenario
            elif item_type == "dataset":
                dataset = DatasetModel.from_json(item)
                datasets[dataset.global_id] = dataset

        if project_obj is None:
            raise ValueError("No project found in response")

        global_id = project_obj["id"]
        name = project_obj["name"]
        network_ids = project_obj.get("networks", [])
        scenario_ids = project_obj.get("scenarios", [])
        dataset_ids = project_obj.get("datasets", [])

        project = ProjectModel(global_id, name, network_ids, scenario_ids, dataset_ids)

        return ResponseModel(project, networks, scenarios, datasets)
