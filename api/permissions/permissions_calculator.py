import typing
from dataclasses import dataclass, field
from functools import reduce

from django.db.models import Q, QuerySet

from environments.permissions.models import (
    UserEnvironmentPermission,
    UserPermissionGroupEnvironmentPermission,
)
from organisations.permissions.models import (
    UserOrganisationPermission,
    UserPermissionGroupOrganisationPermission,
)
from organisations.roles.models import (
    RoleEnvironmentPermission,
    RoleOrganisationPermission,
    RoleProjectPermission,
)
from projects.models import (
    UserPermissionGroupProjectPermission,
    UserProjectPermission,
)

UserPermissionQs = QuerySet[
    typing.Union[
        UserProjectPermission, UserEnvironmentPermission, UserOrganisationPermission
    ]
]

GroupPermissionQs = QuerySet[
    typing.Union[
        UserPermissionGroupProjectPermission,
        UserPermissionGroupEnvironmentPermission,
        UserPermissionGroupOrganisationPermission,
    ]
]

RolePermissionQs = QuerySet[
    typing.Union[
        RoleProjectPermission, RoleEnvironmentPermission, RoleOrganisationPermission
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


@dataclass
class _ProjectPermissionQs:
    project_id: int
    user_id: int

    @property
    def user_qs(self) -> UserPermissionQs:
        return UserProjectPermission.objects.filter(
            project_id=self.project_id, user_id=self.user_id
        )

    @property
    def group_qs(self) -> GroupPermissionQs:
        return UserPermissionGroupProjectPermission.objects.filter(
            group__users=self.user_id, project=self.project_id
        )

    @property
    def role_qs(self) -> RolePermissionQs:
        q = Q(role__userrole__user=self.user_id) | Q(
            role__grouprole__group__users=self.user_id
        )
        q = q & Q(project=self.project_id)
        return RoleProjectPermission.objects.filter(q)


def get_project_permission_data(project_id: int, user_id: int) -> PermissionData:
    project_permission_qs = _ProjectPermissionQs(project_id, user_id)
    return PermissionData(
        user=get_user_permission_data(project_permission_qs.user_qs),
        groups=get_groups_permission_data(project_permission_qs.group_qs),
        roles=get_roles_permission_data(project_permission_qs.role_qs),
    )


def get_organisation_permission_data(organisation_id: int, user) -> PermissionData:
    org_permission_qs = _OrganisationPermissionQs(organisation_id, user.id)
    return PermissionData(
        is_organisation_admin=user.is_organisation_admin(organisation_id),
        user=get_user_permission_data(org_permission_qs.user_qs),
        groups=get_groups_permission_data(org_permission_qs.group_qs),
        roles=get_roles_permission_data(org_permission_qs.role_qs),
    )


def get_environment_permission_data(
    environment_id: int, user_id: int
) -> PermissionData:
    environment_permission_qs = _EnvironmentPermissionQs(environment_id, user_id)
    return PermissionData(
        user=get_user_permission_data(environment_permission_qs.user_qs),
        groups=get_groups_permission_data(environment_permission_qs.group_qs),
        roles=get_roles_permission_data(environment_permission_qs.role_qs),
    )


def _is_organisation_admin(organisation_id, user_id) -> bool:
    # # TODO: implement
    return False


def get_user_permission_data(
    user_permission_qs: UserPermissionQs,
) -> UserPermissionData:
    user_permission_data = UserPermissionData()

    for user_permission in user_permission_qs.prefetch_related("permissions"):
        if getattr(user_permission, "admin", False):
            user_permission_data.admin = True

        user_permission_data.permissions.update(
            permission.key
            for permission in user_permission.permissions.all()
            if permission.key
        )

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

        if getattr(group_permission, "admin", False):
            group_permission_data_object.admin = True

        group_permission_data_object.permissions.update(
            permission.key
            for permission in group_permission.permissions.all()
            if permission.key
        )

        group_permission_data_objects.append(group_permission_data_object)

    return group_permission_data_objects


def get_roles_permission_data(
    role_permission_qs: RolePermissionQs,
) -> typing.List[RolePermissionData]:
    role_permission_data_objects = []

    for role_project_permission in role_permission_qs.select_related(
        "role"
    ).prefetch_related("permissions"):
        role_data = RoleData(
            id=role_project_permission.role.id,
            name=role_project_permission.role.name,
        )
        role_permission_data_object = RolePermissionData(role=role_data)

        if getattr(role_project_permission, "admin", False):
            role_permission_data_object.admin = True

        role_permission_data_object.permissions.update(
            permission.key
            for permission in role_project_permission.permissions.all()
            if permission.key
        )

        role_permission_data_objects.append(role_permission_data_object)

    return role_permission_data_objects


@dataclass
class _OrganisationPermissionQs:
    organisation_id: int
    user_id: int

    @property
    def user_qs(self) -> UserPermissionQs:
        return UserOrganisationPermission.objects.filter(
            user=self.user_id, organisation_id=self.organisation_id
        )

    @property
    def group_qs(self) -> GroupPermissionQs:
        return UserPermissionGroupOrganisationPermission.objects.filter(
            group__users=self.user_id, organisation=self.organisation_id
        )

    @property
    def role_qs(self) -> RolePermissionQs:
        q = Q(role__userrole__user_id=self.user_id) | Q(
            role__grouprole__group__users=self.user_id
        )
        q = q & Q(role__organisation_id=self.organisation_id)
        return RoleOrganisationPermission.objects.filter(q)


@dataclass
class _EnvironmentPermissionQs:
    environment_id: int
    user_id: int

    @property
    def user_qs(self) -> UserPermissionQs:
        return UserEnvironmentPermission.objects.filter(
            user_id=self.user_id, environment_id=self.environment_id
        )

    @property
    def group_qs(self) -> GroupPermissionQs:
        return UserPermissionGroupEnvironmentPermission.objects.filter(
            group__users=self.user_id, environment=self.environment_id
        )

    @property
    def role_qs(self) -> RolePermissionQs:
        q = Q(role__userrole__user=self.user_id) | Q(
            role__grouprole__group__users=self.user_id
        )
        q = q & Q(environment=self.environment_id)
        return RoleEnvironmentPermission.objects.filter(q)
