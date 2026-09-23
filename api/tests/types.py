from datetime import datetime
from typing import Callable, Literal, Optional, Protocol

from django_test_migrations.migrator import Migrator

from environments.models import Environment
from environments.permissions.models import UserEnvironmentPermission
from organisations.permissions.models import UserOrganisationPermission
from projects.models import UserProjectPermission
from segments.types import SegmentRule

_SegmentRulesModifier = Callable[[list[SegmentRule]], None]
InvalidSegmentRulesCase = tuple[_SegmentRulesModifier, dict[str, object]]

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


class EnableFeaturesFixture(Protocol):
    def __call__(self, *feature_names: str) -> None: ...


class MigratorFactory(Protocol):
    def __call__(self, name: Optional[str] = None) -> Migrator: ...


class CreateSegmentOverrideFixture(Protocol):
    def __call__(
        self,
        environment_api_key: str,
        feature_id: int,
        segment_id: int,
        enabled: bool = True,
        priority: int | None = None,
    ) -> None: ...


class CreateChangeRequestSegmentOverrideFixture(Protocol):
    def __call__(
        self,
        environment: Environment,
        feature_id: int,
        segment_id: int,
        committed: bool = False,
        live_from: datetime | None = None,
    ) -> None: ...
