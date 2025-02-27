class RoutingNetwork(object):
    def __init__(self, snapshot_name: str=None, branch_id: str=None):
        self.snapshot_name = snapshot_name
        self.branch_id = branch_id

        if branch_id is None and snapshot_name is None:
            raise ValueError("Either snapshot_name or branch_id must be specified")
