from .BranchCommitModel import BranchCommitModel

class BranchModel(object):
    def __init__(self, global_id: str, commit_model: BranchCommitModel) -> None:
        self.global_id = global_id
        self.commit_model = commit_model

    @staticmethod
    def from_json(json) -> 'BranchModel':
            return BranchModel(json["id"], BranchCommitModel.from_json(json['commit']))