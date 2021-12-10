import typing

from rest_framework.test import APIClient

from environments.models import Environment
from environments.permissions.models import (
    EnvironmentPermissionModel,
    UserEnvironmentPermission,
)
from projects.models import ProjectPermissionModel, UserProjectPermission
from users.models import FFAdminUser


def get_environment_user_client(
    user: FFAdminUser,
    environment: Environment,
    permission_keys: typing.List[str] = None,
    admin: bool = False,
) -> APIClient:
    """
    Update provided user with given permissions and return an authenticated client
    """

    view_project_permission = ProjectPermissionModel.objects.get(key="VIEW_PROJECT")
    user_project_permission = UserProjectPermission.objects.create(
        user=user, project=environment.project
    )
    user_project_permission.permissions.add(view_project_permission)

    user_permission = UserEnvironmentPermission.objects.create(
        user=user, environment=environment, admin=admin
    )
    if permission_keys:
        user_permission.permissions.add(
            *list(EnvironmentPermissionModel.objects.filter(key__in=permission_keys))
        )
        user_permission.save()

    client = APIClient()
    client.force_authenticate(user)
    return client
