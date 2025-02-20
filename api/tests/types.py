from typing import Callable, Literal

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
