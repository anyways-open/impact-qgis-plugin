from collections.abc import Callable

from .RouteResult import RouteResult
from ..Matrix import Matrix
from ..RoutingNetwork import RoutingNetwork

class RoutingTaskSettings(object):
  def __init__(self, name: str, network: RoutingNetwork, profile: str, matrix: Matrix, callback: Callable[[list[RouteResult]], None], get_token=None, on_error=None):
    self.name = name
    self.profile = profile
    self.network = network
    self.matrix = matrix
    self.callback = callback
    self.get_token = get_token
    self.on_error = on_error
