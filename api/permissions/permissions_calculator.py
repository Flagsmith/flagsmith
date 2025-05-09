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
    Project,
    UserPermissionGroupProjectPermission,
    UserProjectPermission,
)

from .rbac_wrapper import (  # type: ignore[attr-defined]
    get_roles_permission_data_for_environment,
    get_roles_permission_data_for_organisation,
    get_roles_permission_data_for_project,
)

if typing.TYPE_CHECKING:
    from environments.models import Environment
    from users.models import FFAdminUser

# Some random comment
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


@dataclass(kw_only=True)
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
    tags: typing.Set[int]


@dataclass
class RolePermissionData(
    _PermissionDataBase,
):
    role: RoleData


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
    derived_from: PermissionDerivedFromData
    is_directly_granted: bool
    permissions: typing.List[DetailedPermissionsData]


@dataclass
class PermissionData:
    """
    Dataclass to hold the permissions of a user w.r.t. a project, environment or organisation.
    """

    user: UserPermissionData
    groups: typing.List[GroupPermissionData]
    roles: typing.List[RolePermissionData]
    is_organisation_admin: bool = False
    admin_override: bool = False
    inherited_admin_groups: typing.List[GroupPermissionData] = field(
        default_factory=list
    )
    inherited_admin_roles: typing.List[RolePermissionData] = field(default_factory=list)

    @property
    def admin(self) -> bool:
        return bool(
            self.is_organisation_admin
            or self.user.admin
            or any(group.admin for group in self.groups)
            or any(role.admin for role in self.roles)
            or self.admin_override
            or self.inherited_admin_groups
            or self.inherited_admin_roles
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

    def to_detailed_permissions_data(self) -> UserDetailedPermissionsData:  # noqa: C901
        permission_map = {}
        is_admin_permission_directly_granted = False
        admin_permission_derived_from = PermissionDerivedFromData()

        def add_permission(
            permission_key: str,
            group: typing.Optional[GroupData],
            role: typing.Optional[RoleData],
        ) -> None:
            if permission_key not in permission_map:
                permission_map[permission_key] = DetailedPermissionsData(
                    permission_key=permission_key,
                    is_directly_granted=bool(group is None and role is None),
                    derived_from=PermissionDerivedFromData(),
                )
            if group:
                permission_map[permission_key].derived_from.groups.append(group)
            if role:
                permission_map[permission_key].derived_from.roles.append(role)

        # Add user's direct permissions
        for permission_key in self.user.permissions:
            if self.user.admin:
                is_admin_permission_directly_granted = True

            add_permission(permission_key, None, None)

        # Add group permissions
        for group_permission in self.groups:
            if group_permission.admin:
                admin_permission_derived_from.groups.append(group_permission.group)

            for permission_key in group_permission.permissions:
                add_permission(permission_key, group_permission.group, None)

        # Add role permissions
        for role_permission in self.roles:
            if role_permission.admin:
                admin_permission_derived_from.roles.append(role_permission.role)

            for permission_key in role_permission.permissions:
                add_permission(permission_key, None, role_permission.role)

        if self.is_organisation_admin or self.user.admin or self.admin_override:
            is_admin_permission_directly_granted = True

        return UserDetailedPermissionsData(
            admin=self.admin,
            is_directly_granted=is_admin_permission_directly_granted,
            derived_from=admin_permission_derived_from,
            permissions=list(permission_map.values()),
        )


def get_organisation_permission_data(
    organisation_id: int, user: "FFAdminUser"
) -> PermissionData:
    org_permission_svc = _OrganisationPermissionService(organisation_id, user.id)
    return PermissionData(
        is_organisation_admin=user.is_organisation_admin(organisation_id),
        groups=get_groups_permission_data(org_permission_svc.group_qs),
        user=get_user_permission_data(org_permission_svc.user_permission),  # type: ignore[arg-type]
        roles=org_permission_svc.roles,
    )


def get_project_permission_data(
    project: Project, user: "FFAdminUser"
) -> PermissionData:
    project_permission_svc = _ProjectPermissionService(project.id, user.id)
    return PermissionData(
        is_organisation_admin=user.is_organisation_admin(project.organisation_id),
        groups=get_groups_permission_data(project_permission_svc.group_qs),
        user=get_user_permission_data(project_permission_svc.user_permission),  # type: ignore[arg-type]
        roles=project_permission_svc.roles,
    )


def get_environment_permission_data(
    environment: "Environment", user: "FFAdminUser"
) -> PermissionData:
    project_permission_svc = _ProjectPermissionService(environment.project_id, user.id)
    environment_permission_svc = _EnvironmentPermissionService(
        environment.id, user.id, project_permission_svc=project_permission_svc
    )

    return PermissionData(
        is_organisation_admin=user.is_organisation_admin(
            environment.project.organisation_id
        ),
        groups=get_groups_permission_data(environment_permission_svc.group_qs),
        user=get_user_permission_data(environment_permission_svc.user_permission),  # type: ignore[arg-type]
        roles=environment_permission_svc.roles_data,
        inherited_admin_groups=get_groups_permission_data(
            environment_permission_svc.inherited_admin_group_qs
        ),
        inherited_admin_roles=environment_permission_svc.inherited_admin_roles,
        admin_override=environment_permission_svc.inherited_user_admin,
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

    @property
    def roles(self) -> typing.List[RolePermissionData]:
        roles_permission_data: typing.List[RolePermissionData] = (
            get_roles_permission_data_for_organisation(
                self.organisation_id, self.user_id
            )
        )
        return roles_permission_data


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

    @property
    def roles(self) -> typing.List[RolePermissionData]:
        roles_permission_data: typing.List[RolePermissionData] = (
            get_roles_permission_data_for_project(self.project_id, self.user_id)
        )
        return roles_permission_data


@dataclass
class _EnvironmentPermissionService:
    environment_id: int
    user_id: int
    project_permission_svc: _ProjectPermissionService

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

    @property
    def roles_data(self) -> typing.List[RolePermissionData]:
        roles_permission_data: typing.List[RolePermissionData] = (
            get_roles_permission_data_for_environment(self.environment_id, self.user_id)
        )
        return roles_permission_data

    @property
    def inherited_user_admin(self) -> bool:
        if user_permission := self.project_permission_svc.user_permission:
            return user_permission.admin
        return False

    @property
    def inherited_admin_group_qs(self) -> GroupPermissionQs:
        return self.project_permission_svc.group_qs.filter(admin=True)

    @property
    def inherited_admin_roles(self) -> typing.List[RolePermissionData]:
        return [role for role in self.project_permission_svc.roles if role.admin]
