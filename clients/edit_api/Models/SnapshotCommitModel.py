class SnapshotCommitModel(object):
    def __init__(self, global_id: str) -> None:
        self.global_id = global_id

    @staticmethod
    def from_json(json) -> 'SnapshotCommitModel':
        return SnapshotCommitModel(json["id"])