from collections.abc import Callable

from ...Result import Result
from ...clients.publish_api.Models.RouteResponse import RouteResponse
from ..Matrix import Matrix
from ..RoutingNetwork import RoutingNetwork

class NetworkCommit(object):
  def __init__(self, branch_commit_id=None, snapshot_commit_id=None):
    self.branch_commit_id = branch_commit_id
    self.snapshot_commit_id = snapshot_commit_id

    if snapshot_commit_id is None and branch_commit_id is None:
      raise ValueError("Either snapshot_commit_id or branch_commit_id must be specified")


  def __repr__(self):
    if self.snapshot_commit_id is None:
      return f"<NetworkCommit: BranchCommit {self.branch_commit_id}>"
    return f"<NetworkCommit: SnapshotCommit {self.snapshot_commit_id}>"

class RoutingTaskSettings(object):
  def __init__(self, network: RoutingNetwork, profile: str, matrix: Matrix, callback: Callable[[list[Result[RouteResponse]]], None]):
    self.profile = profile
    self.network = network
    self.matrix = matrix
    self.callback = callback