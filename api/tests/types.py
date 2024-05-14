from typing import Callable

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
