from typing import Protocol


class GetEnvironmentFlagsResponseJSONCallable(Protocol):
    def __call__(self, num_expected_flags: int) -> dict: ...


class GetIdentityFlagsResponseJSONCallable(Protocol):
    def __call__(
        self,
        num_expected_flags: int,
        identity_identifier: str = "test-identity",
        **traits,
    ) -> dict: ...
