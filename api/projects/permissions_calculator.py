import typing
from dataclasses import dataclass

from projects.models import (
    UserPermissionGroupProjectPermission,
    UserProjectPermission,
)


@dataclass
class UserProjectPermissionData:
    admin: bool
    permissions: typing.Set[str]


class ProjectPermissionsCalculator:
    @classmethod
    def get_user_project_permission_data(
        cls, user_id: int, project_id: int
    ) -> UserProjectPermissionData:
        admin = False
        permissions = set()

        user_permissions = UserProjectPermission.objects.filter(
            user=user_id, project=project_id
        ).prefetch_related("permissions")

        group_permissions = UserPermissionGroupProjectPermission.objects.filter(
            group__users=user_id, project=project_id
        ).prefetch_related("permissions")

        for user_or_group_permission in [*user_permissions, *group_permissions]:
            if user_or_group_permission.admin:
                admin = True

            permissions.update(
                {
                    permission.key
                    for permission in user_or_group_permission.permissions.all()
                    if permission.key
                }
            )

        return UserProjectPermissionData(admin=admin, permissions=permissions)
