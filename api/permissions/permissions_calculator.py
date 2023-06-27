import typing
from dataclasses import dataclass, field
from functools import reduce

from django.db.models import QuerySet

from environments.permissions.models import (
    UserEnvironmentPermission,
    UserPermissionGroupEnvironmentPermission,
)
from organisations.permissions.models import (
    UserOrganisationPermission,
    UserPermissionGroupOrganisationPermission,
)
from projects.models import (
    UserPermissionGroupProjectPermission,
    UserProjectPermission,
)

from .rbac_wrapper import (
    RolePermissionData,
    get_roles_permission_data_for_environment,
    get_roles_permission_data_for_organisation,
    get_roles_permission_data_for_project,
)

UserPermissionType = typing.Union[
    UserProjectPermission, UserEnvironmentPermission, UserOrganisationPermission
]

GroupPermissionQs = QuerySet[
    typing.Union[
        UserPermissionGroupProjectPermission,
        UserPermissionGroupEnvironmentPermission,
        UserPermissionGroupOrganisationPermission,
    ]
]


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
class PermissionData:
    """
    Dataclass to hold the permissions of a user w.r.t. a project, environment or organisation.
    """

    user: UserPermissionData
    groups: typing.List[GroupPermissionData]
    roles: typing.List[
        "RolePermissionData" if "RolePermissionData" in globals() else typing.Any
    ]
    is_organisation_admin: bool = False

    @property
    def admin(self) -> bool:
        return (
            self.is_organisation_admin
            or self.user.admin
            or any(group.admin for group in self.groups)
            or any(role.admin for role in self.roles)
        )

    @property
    def permissions(self) -> typing.Set[str]:
        # Returns a set of all permissions that the user has based on their direct permissions,
        # group permissions, and role permissions.
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


def get_project_permission_data(project_id: int, user_id: int) -> PermissionData:
    project_permission_svc = _ProjectPermissionService(project_id, user_id)
    return PermissionData(
        groups=get_groups_permission_data(project_permission_svc.group_qs),
        user=get_user_permission_data(project_permission_svc.user_permission),
        roles=get_roles_permission_data_for_project(project_id, user_id),
    )


def get_organisation_permission_data(organisation_id: int, user) -> PermissionData:
    org_permission_svc = _OrganisationPermissionService(organisation_id, user.id)
    return PermissionData(
        is_organisation_admin=user.is_organisation_admin(organisation_id),
        groups=get_groups_permission_data(org_permission_svc.group_qs),
        user=get_user_permission_data(org_permission_svc.user_permission),
        roles=get_roles_permission_data_for_organisation(organisation_id, user.id),
    )


def get_environment_permission_data(
    environment_id: int, user_id: int
) -> PermissionData:
    environment_permission_svc = _EnvironmentPermissionService(environment_id, user_id)
    return PermissionData(
        groups=get_groups_permission_data(environment_permission_svc.group_qs),
        user=get_user_permission_data(environment_permission_svc.user_permission),
        roles=get_roles_permission_data_for_environment(environment_id, user_id),
    )


def get_user_permission_data(user_permission: UserPermissionType) -> UserPermissionData:
    user_permission_data = UserPermissionData()
    user_permission_data.permissions.update(
        permission.key
        for permission in user_permission.permissions.all()
        if permission.key
    )
    user_permission_data.admin = getattr(user_permission, "admin", False)

    return user_permission_data


def get_groups_permission_data(
    group_permission_qs: GroupPermissionQs,
) -> typing.List[GroupPermissionData]:
    user_permission_group_permission_objects = group_permission_qs.select_related(
        "group"
    ).prefetch_related("permissions")

    group_permission_data_objects = []

    for group_permission in user_permission_group_permission_objects:
        group = group_permission.group
        group_data = GroupData(id=group.id, name=group.name)
        group_permission_data_object = GroupPermissionData(group=group_data)

        group_permission_data_object.admin = getattr(group_permission, "admin", False)

        group_permission_data_object.permissions.update(
            permission.key
            for permission in group_permission.permissions.all()
            if permission.key
        )

        group_permission_data_objects.append(group_permission_data_object)

    return group_permission_data_objects


@dataclass
class _OrganisationPermissionService:
    organisation_id: int
    user_id: int

    @property
    def user_permission(self) -> UserOrganisationPermission:
        return UserOrganisationPermission.objects.get(
            user=self.user_id, organisation_id=self.organisation_id
        )

    @property
    def group_qs(self) -> GroupPermissionQs:
        return UserPermissionGroupOrganisationPermission.objects.filter(
            group__users=self.user_id, organisation=self.organisation_id
        )


@dataclass
class _EnvironmentPermissionService:
    environment_id: int
    user_id: int

    @property
    def user_permission(self) -> UserEnvironmentPermission:
        return UserEnvironmentPermission.objects.get(
            user_id=self.user_id, environment_id=self.environment_id
        )

    @property
    def group_qs(self) -> GroupPermissionQs:
        return UserPermissionGroupEnvironmentPermission.objects.filter(
            group__users=self.user_id, environment=self.environment_id
        )


@dataclass
class _ProjectPermissionService:
    project_id: int
    user_id: int

    @property
    def user_permission(self) -> UserProjectPermission:
        return UserProjectPermission.objects.get(
            project_id=self.project_id, user_id=self.user_id
        )

    @property
    def group_qs(self) -> GroupPermissionQs:
        return UserPermissionGroupProjectPermission.objects.filter(
            group__users=self.user_id, project=self.project_id
        )
