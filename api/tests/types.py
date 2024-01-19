from typing import Callable

from environments.permissions.models import UserEnvironmentPermission
from projects.models import Project, UserProjectPermission

WithProjectPermissionsCallable = Callable[
    [list[str], Project | None], UserProjectPermission
]
WithEnvironmentPermissionsCallable = Callable[
    [list[str], Project | None], UserEnvironmentPermission
]
