import typing
from dataclasses import dataclass, field
from functools import reduce

from projects.models import (
    UserPermissionGroupProjectPermission,
    UserProjectPermission,
)


@dataclass
class _PermissionDataBase:
    admin: bool = False
    permissions: typing.Set[str] = field(default_factory=set)


@dataclass
class GroupData:
    id: int
    name: str


@dataclass
class _GroupPermissionBase:
    group: GroupData


@dataclass
class UserPermissionData(_PermissionDataBase):
    pass


@dataclass
class GroupPermissionData(_PermissionDataBase, _GroupPermissionBase):
    pass


@dataclass
class UserProjectPermissionData:
    user: UserPermissionData
    groups: typing.List[GroupPermissionData]

    @property
    def admin(self) -> bool:
        return self.user.admin or any(group.admin for group in self.groups)

    @property
    def permissions(self) -> typing.Set[str]:
        return self.user.permissions.union(
            reduce(
                lambda a, b: a.union(b),
                [group.permissions for group in self.groups],
                set(),
            )
        )


class ProjectPermissionsCalculator:
    def __init__(self, project_id: int):
        self.project_id = project_id

    def get_user_project_permission_data(
        self, user_id: int
    ) -> UserProjectPermissionData:
        return UserProjectPermissionData(
            user=self._get_user_permission_data(user_id),
            groups=self._get_groups_permission_data(user_id),
        )

    def _get_user_permission_data(self, user_id: int) -> UserPermissionData:
        user_permission_data = UserPermissionData()

        for user_permission in UserProjectPermission.objects.filter(
            user=user_id, project=self.project_id
        ).prefetch_related("permissions"):
            if user_permission.admin:
                user_permission_data.admin = True

            user_permission_data.permissions.update(
                permission.key
                for permission in user_permission.permissions.all()
                if permission.key
            )

        return user_permission_data

    def _get_groups_permission_data(
        self, user_id: int
    ) -> typing.List[GroupPermissionData]:
        user_permission_group_project_permission_objects = (
            UserPermissionGroupProjectPermission.objects.filter(
                group__users=user_id, project=self.project_id
            )
            .select_related("group")
            .prefetch_related("permissions")
        )

        group_permission_data_objects = []

        for group_permission in user_permission_group_project_permission_objects:
            group = group_permission.group
            group_data = GroupData(id=group.id, name=group.name)
            group_permission_data_object = GroupPermissionData(group=group_data)

            if group_permission.admin:
                group_permission_data_object.admin = True

            group_permission_data_object.permissions.update(
                permission.key
                for permission in group_permission.permissions.all()
                if permission.key
            )

            group_permission_data_objects.append(group_permission_data_object)

        return group_permission_data_objects
