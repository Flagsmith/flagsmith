from typing import Protocol


class GetEnvironmentFlagsResponseJSONCallable(Protocol):
    def __call__(self, num_expected_flags: int) -> dict: ...  # type: ignore[type-arg]


class GetIdentityFlagsResponseJSONCallable(Protocol):
    def __call__(  # type: ignore[no-untyped-def]
        self,
        num_expected_flags: int,
        identity_identifier: str = "test-identity",
        **traits,
    ) -> dict: ...  # type: ignore[type-arg]
