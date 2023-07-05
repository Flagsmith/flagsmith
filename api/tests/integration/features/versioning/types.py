from typing import Protocol


class GetResponseJSONCallable(Protocol):
    def __call__(self, num_expected_flags: int) -> dict:
        ...
