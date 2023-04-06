import typing
from dataclasses import dataclass, field
from functools import reduce

from django.db.models import Q

from environments.permissions.models import (
    UserEnvironmentPermission,
    UserPermissionGroupEnvironmentPermission,
)
from organisations.roles.models import (
    RoleEnvironmentPermission,
    RoleProjectPermission,
)
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
class PermissionData:
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


class BasePermissionCalculator:
    pk_name = None

    def __init__(self, pk: int):
        self.pk = pk

    def _get_user_permission_qs(self, user_id: int):
        raise NotImplementedError()

    def _get_group_permission_qs(self, user_id: int):
        raise NotImplementedError()

    def _get_role_permission_qs(self, user_id: int):
        raise NotImplementedError()

    def get_permission_data(self, user_id: int) -> PermissionData:
        return PermissionData(
            user=self._get_user_permission_data(user_id),
            groups=self._get_groups_permission_data(user_id),
            roles=self._get_roles_permission_data(user_id),
        )

    def _get_user_permission_data(self, user_id: int) -> PermissionData:
        user_permission_data = UserPermissionData()

        for user_permission in self._get_user_permission_qs(user_id).prefetch_related(
            "permissions"
        ):
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
        user_permission_group_permission_objects = (
            self._get_group_permission_qs(user_id)
            .select_related("group")
            .prefetch_related("permissions")
        )

        group_permission_data_objects = []

        for group_permission in user_permission_group_permission_objects:
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

        role_permission_data_objects = []

        for role_project_permission in (
            self._get_role_permission_qs(user_id)
            .select_related("role")
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


class EnvironmentPermissionsCalculator(BasePermissionCalculator):
    def _get_user_permission_qs(self, user_id: int):
        return UserEnvironmentPermission.objects.filter(
            user=user_id, environment_id=self.pk
        )

    def _get_group_permission_qs(self, user_id: int):
        return UserPermissionGroupEnvironmentPermission.objects.filter(
            group__users=user_id, environment=self.pk
        )

    def _get_role_permission_qs(self, user_id: int):
        q = Q(role__userrole__user=user_id) | Q(role__grouprole__group__users=user_id)
        q = q & Q(environment=self.pk)
        return RoleEnvironmentPermission.objects.filter(q)


class ProjectPermissionsCalculator(BasePermissionCalculator):
    def _get_user_permission_qs(self, user_id: int):
        return UserProjectPermission.objects.filter(user=user_id, project_id=self.pk)

    def _get_group_permission_qs(self, user_id: int):
        return UserPermissionGroupProjectPermission.objects.filter(
            group__users=user_id, project=self.pk
        )

    def _get_role_permission_qs(self, user_id: int):
        q = Q(role__userrole__user=user_id) | Q(role__grouprole__group__users=user_id)
        q = q & Q(project=self.pk)
        return RoleProjectPermission.objects.filter(q)
