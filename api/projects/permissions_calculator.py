import typing
from dataclasses import dataclass, field
from functools import reduce

from django.db.models import Q

from organisations.roles.models import RoleProjectPermission
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
class RoleData:
    id: int
    name: str


@dataclass
class _GroupPermissionBase:
    group: GroupData


@dataclass
class _RolePermissionBase:
    role: RoleData


@dataclass
class UserPermissionData(_PermissionDataBase):
    pass


@dataclass
class GroupPermissionData(_PermissionDataBase, _GroupPermissionBase):
    pass


@dataclass
class RolePermissionData(_PermissionDataBase, _RolePermissionBase):
    pass


@dataclass
class UserProjectPermissionData:
    user: UserPermissionData
    groups: typing.List[GroupPermissionData]
    roles: typing.List[RolePermissionData]

    @property
    def admin(self) -> bool:
        return (
            self.user.admin
            or any(group.admin for group in self.groups)
            or any(role.admin for role in self.roles)
        )

    @property
    def permissions(self) -> typing.Set[str]:
        return self.user.permissions.union(
            reduce(
                lambda a, b: a.union(b),
                [group.permissions for group in self.groups],
                set(),
            )
        ).union(
            reduce(
                lambda a, b: a.union(b),
                [role.permissions for role in self.roles],
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
            roles=self._get_roles_permission_data(user_id),
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

    def _get_roles_permission_data(
        self, user_id: int
    ) -> typing.List[RolePermissionData]:
        pass

        q = Q(role__userrole__user_id=user_id) | Q(
            role__grouprole__group__user_id=user_id
        )
        role_permission_data_objects = []
        for role_project_permission in (
            RoleProjectPermission.objects.filter(q)
            .selet_related("role")
            .prefetch_related("permissions")
        ):
            role_data = RoleData(
                id=role_project_permission.role.id,
                name=role_project_permission.role.name,
            )
            role_permission_data_object = RolePermissionData(role=role_data)

            if role_project_permission.admin:
                role_permission_data_object.admin = True

            role_permission_data_object.permissions.update(
                permission.key
                for permission in role_project_permission.permissions.all()
                if permission.key
            )

            role_permission_data_objects.append(role_permission_data_object)

        return role_permission_data_objects
