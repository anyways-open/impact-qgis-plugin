from typing import TypeVar, Generic

from .DatasetModel import DatasetModel
from .NetworkModel import NetworkModel
from .ScenarioModel import ScenarioModel

T = TypeVar('T')

class ResponseModel(Generic[T]):
    def __init__(self, details: T, networks: dict[str, NetworkModel], scenarios: dict[str, ScenarioModel], datasets: dict[str, DatasetModel] = None) -> None:
        self.details = details
        self.networks = networks
        self.scenarios = scenarios
        self.datasets = datasets or dict()