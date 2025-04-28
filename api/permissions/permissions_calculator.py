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

from .permission_service import is_user_project_admin
from .rbac_wrapper import (  # type: ignore[attr-defined]
    RolePermissionData,
    get_roles_permission_data_for_environment,
    get_roles_permission_data_for_organisation,
    get_roles_permission_data_for_project,
)

if typing.TYPE_CHECKING:
    from environments.models import Environment
    from users.models import FFAdminUser


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
class RoleData:
    id: int
    name: str
    tags: typing.List[int]


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
class PermissionDerivedFromData:
    groups: typing.List[GroupData] = field(default_factory=list)
    roles: typing.List[RoleData] = field(default_factory=list)


@dataclass
class DetailedPermissionsData:
    permission_key: str
    is_directly_granted: bool
    derived_from: PermissionDerivedFromData


@dataclass
class UserDetailedPermissionsData:
    admin: bool
    permissions: typing.List[DetailedPermissionsData]


@dataclass
class PermissionData:
    """
    Dataclass to hold the permissions of a user w.r.t. a project, environment or organisation.
    """

    user: UserPermissionData
    groups: typing.List[GroupPermissionData]
    roles: typing.List[  # type: ignore[valid-type]
        "RolePermissionData" if "RolePermissionData" in globals() else typing.Any
    ]
    is_organisation_admin: bool = False
    admin_override: bool = False

    @property
    def admin(self) -> bool:
        return (
            self.is_organisation_admin
            or self.user.admin
            or any(group.admin for group in self.groups)
            or any(role.admin for role in self.roles)
            or self.admin_override
        )

    @property
    def permissions(self) -> typing.Set[str]:
        # Returns a set of all permissions that the user has based on their direct permissions,
        # group permissions, and role permissions.
        return self.user.permissions.union(
            reduce(
                lambda a, b: a.union(b),  # type: ignore[arg-type,return-value]
                [group.permissions for group in self.groups],
                set(),
            )
        ).union(
            reduce(
                lambda a, b: a.union(b),  # type: ignore[attr-defined]
                [
                    role_permission.permissions
                    for role_permission in self.roles
                    if not role_permission.role.tags
                ],
                set(),
            )
        )

    @property
    def tag_based_permissions(self) -> list[dict]:  # type: ignore[type-arg]
        return [
            {
                "permissions": role_permission.permissions,
                "tags": role_permission.role.tags,
            }
            for role_permission in self.roles
            if role_permission.role.tags
        ]

    def to_detailed_permissions_data(self) -> UserDetailedPermissionsData:
        permission_map = {}

        def add_permission(
            perm_key: str,
            group: typing.Optional[int],
            role: typing.Optional[int],
        ):
            if perm_key not in permission_map:
                permission_map[perm_key] = DetailedPermissionsData(
                    permission_key=perm_key,
                    is_directly_granted=group is None and role is None,
                    derived_from=PermissionDerivedFromData(),
                )
            if group:
                permission_map[perm_key].derived_from.groups.append(group)
            if role:
                permission_map[perm_key].derived_from.roles.append(role)

        # Add user's direct permissions
        for perm in self.user.permissions:
            add_permission(perm, [], None)

        # Add group permissions
        for group in self.groups:
            for perm in group.permissions:
                add_permission(perm, group, None)

        # Add role permissions
        for role_permission in self.roles:
            for perm in role_permission.permissions:
                add_permission(perm, None, role_permission.role)

        return UserDetailedPermissionsData(
            admin=self.admin, permissions=list(permission_map.values())
        )


def get_project_permission_data(project_id: int, user_id: int) -> PermissionData:
    project_permission_svc = _ProjectPermissionService(project_id, user_id)
    return PermissionData(
        groups=get_groups_permission_data(project_permission_svc.group_qs),
        user=get_user_permission_data(project_permission_svc.user_permission),  # type: ignore[arg-type]
        roles=get_roles_permission_data_for_project(project_id, user_id),
    )


def get_organisation_permission_data(
    organisation_id: int, user: "FFAdminUser"
) -> PermissionData:
    org_permission_svc = _OrganisationPermissionService(organisation_id, user.id)
    return PermissionData(
        is_organisation_admin=user.is_organisation_admin(organisation_id),
        groups=get_groups_permission_data(org_permission_svc.group_qs),
        user=get_user_permission_data(org_permission_svc.user_permission),  # type: ignore[arg-type]
        roles=get_roles_permission_data_for_organisation(organisation_id, user.id),
    )


def get_environment_permission_data(
    environment: "Environment", user: "FFAdminUser"
) -> PermissionData:
    environment_permission_svc = _EnvironmentPermissionService(environment.id, user.id)
    return PermissionData(
        groups=get_groups_permission_data(environment_permission_svc.group_qs),
        user=get_user_permission_data(environment_permission_svc.user_permission),  # type: ignore[arg-type]
        roles=get_roles_permission_data_for_environment(environment.id, user.id),
        admin_override=is_user_project_admin(user, project=environment.project),
    )


def get_user_permission_data(
    user_permission: UserPermissionType = None,  # type: ignore[assignment]
) -> UserPermissionData:
    user_permission_data = UserPermissionData()
    if not user_permission:
        return user_permission_data

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
    def user_permission(self) -> typing.Optional[UserOrganisationPermission]:
        return UserOrganisationPermission.objects.filter(
            user=self.user_id, organisation_id=self.organisation_id
        ).first()

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
    def user_permission(self) -> typing.Optional[UserEnvironmentPermission]:
        return UserEnvironmentPermission.objects.filter(
            user_id=self.user_id, environment_id=self.environment_id
        ).first()

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
    def user_permission(self) -> typing.Optional[UserProjectPermission]:
        return UserProjectPermission.objects.filter(
            project_id=self.project_id, user_id=self.user_id
        ).first()

    @property
    def group_qs(self) -> GroupPermissionQs:
        return UserPermissionGroupProjectPermission.objects.filter(
            group__users=self.user_id, project=self.project_id
        )
