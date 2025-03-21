class BranchCommitModel(object):
    def __init__(self, global_id: str):
        self.global_id = global_id

    @staticmethod
    def from_json(json) -> 'BranchCommitModel':
        return BranchCommitModel(json["id"])