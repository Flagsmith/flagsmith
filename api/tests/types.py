import typing
from typing import Callable, Literal

from environments.permissions.models import UserEnvironmentPermission
from organisations.permissions.models import UserOrganisationPermission
from projects.models import UserProjectPermission

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


class TestFlagData(typing.NamedTuple):
    feature_name: str
    enabled: bool
    value: typing.Any
