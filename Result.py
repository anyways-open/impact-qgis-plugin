from typing import TypeVar, Generic, List

T = TypeVar('T')

class Result(Generic[T]):
    def __init__(self, result: T=None, message: str=None) -> None:
        self.result = result
        self.message = message

    def is_success(self):
        return self.result is not None