from typing import TypeVar, Generic

from .NetworkModel import NetworkModel
from .ScenarioModel import ScenarioModel

T = TypeVar('T')

class ResponseModel(Generic[T]):
    def __init__(self, details: T, networks: dict[str, NetworkModel], scenarios: dict[str, ScenarioModel]) -> None:
        self.details = details
        self.networks = networks
        self.scenarios = scenarios