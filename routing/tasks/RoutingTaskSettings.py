from collections.abc import Callable

from .RouteResult import RouteResult
from ..Matrix import Matrix
from ..RoutingNetwork import RoutingNetwork

class RoutingTaskSettings(object):
  def __init__(self, name: str, network: RoutingNetwork, profile: str, matrix: Matrix, callback: Callable[[list[RouteResult]], None]):
    self.name = name
    self.profile = profile
    self.network = network
    self.matrix = matrix
    self.callback = callback
