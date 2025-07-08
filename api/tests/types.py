from typing import Any, Callable, Literal, NamedTuple, Protocol

from environments.permissions.models import UserEnvironmentPermission
from organisations.permissions.models import UserOrganisationPermission
from projects.models import UserProjectPermission

# TODO: these type aliases aren't strictly correct according to mypy
#  See here for more details: https://github.com/Flagsmith/flagsmith/issues/5140
WithProjectPermissionsCallable = Callable[
    [list[str] | None, int | None, bool], UserProjectPermission
]
WithOrganisationPermissionsCallable = Callable[
    [list[str], int | None], UserOrganisationPermission
]
WithEnvironmentPermissionsCallable = Callable[
    [list[str] | None, int | None, bool], UserEnvironmentPermission
]

AdminClientAuthType = Literal["user", "master_api_key"]


class GetEnvironmentFlagsResponseJSONCallable(Protocol):
    def __call__(self, num_expected_flags: int) -> dict: ...  # type: ignore[type-arg]


class GetIdentityFlagsResponseJSONCallable(Protocol):
    def __call__(  # type: ignore[no-untyped-def]
        self,
        num_expected_flags: int,
        identity_identifier: str = "test-identity",
        **traits,
    ) -> dict: ...  # type: ignore[type-arg]


class TestFlagData(NamedTuple):
    feature_name: str
    enabled: bool = False
    value: Any = None
