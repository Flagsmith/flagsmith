from typing import TYPE_CHECKING, Union

from django.db.models import Q, QuerySet

from environments.models import Environment
from organisations.models import Organisation, OrganisationRole
from projects.models import Project

from .rbac_wrapper import get_role_permission_filter

if TYPE_CHECKING:
    from users.models import FFAdminUser


def is_user_organisation_admin(
    user: "FFAdminUser", organisation: Union[Organisation, int]
) -> bool:
    user_organisation = user.get_user_organisation(organisation)
    if user_organisation is not None:
        return user_organisation.role == OrganisationRole.ADMIN.name
    return False


def is_user_project_admin(user: "FFAdminUser", project: Project) -> bool:
    return is_user_organisation_admin(
        user, project.organisation
    ) or _is_user_object_admin(user, project)


def is_user_environment_admin(user: "FFAdminUser", environment: Environment) -> bool:
    return is_user_project_admin(user, environment.project) or _is_user_object_admin(
        user, environment
    )


def get_permitted_projects_for_user(
    user: "FFAdminUser", permission_key: str
) -> QuerySet[Project]:
    """
    Get all projects that the user has the given permissions for.

    Rules:
        - User has the required permissions directly (UserProjectPermission)
        - User is in a UserPermissionGroup that has required permissions (UserPermissionGroupProjectPermissions)
        - User is an admin for the organisation the project belongs to
        - User has a role attached with the required permissions(if rbac is enabled)
        - User is in a UserPermissionGroup that has a role attached with the required permissions
    """
    base_filter = get_base_permission_filter(user, Project, permission_key)

    organisation_filter = Q(
        organisation__userorganisation__user=user,
        organisation__userorganisation__role=OrganisationRole.ADMIN.name,
    )
    filter_ = base_filter | organisation_filter
    return Project.objects.filter(filter_).distinct()


def get_permitted_environments_for_user(
    user: "FFAdminUser",
    project: Project,
    permission_key: str,
) -> QuerySet[Environment]:
    """
    Get all environments that the user has the given permissions for.

    Rules:
        - User has the required permissions directly (UserEnvironmentPermission)
        - User is in a UserPermissionGroup that has required permissions (UserPermissionGroupEnvironmentPermissions)
        - User is an admin for the project the environment belongs to
        - User is an admin for the organisation the environment belongs to
        - User has a role attached with the required permissions(if rbac is enabled)
        - User is in a UserPermissionGroup that has a role attached with the required permissions(if rbac is enabled)
    """

    if is_user_project_admin(user, project):
        return project.environments.all()

    base_filter = get_base_permission_filter(user, Environment, permission_key)
    filter_ = base_filter & Q(project=project)

    return Environment.objects.filter(filter_).distinct().defer("description")


def user_has_organisation_permission(
    user: "FFAdminUser", organisation: Organisation, permission_key: str
) -> bool:
    if is_user_organisation_admin(user, organisation):
        return True

    base_filter = get_base_permission_filter(
        user, Organisation, permission_key, allow_admin=False
    )
    filter_ = base_filter & Q(id=organisation.id)

    return Organisation.objects.filter(filter_).exists()


def _is_user_object_admin(
    user: "FFAdminUser", object_: Union[Project, Environment]
) -> bool:
    ModelClass = type(object_)
    base_filter = get_base_permission_filter(user, ModelClass)
    filter_ = base_filter & Q(id=object_.id)
    return ModelClass.objects.filter(filter_).exists()


def get_base_permission_filter(
    user: "FFAdminUser",
    for_model: Union[Organisation, Project, Environment] = None,
    permission_key: str = None,
    allow_admin: bool = True,
) -> Q:
    user_filter = get_user_permission_filter(user, permission_key, allow_admin)
    group_filter = get_group_permission_filter(user, permission_key, allow_admin)

    role_filter = get_role_permission_filter(
        user, for_model, permission_key, allow_admin
    )

    return user_filter | group_filter | role_filter


def get_user_permission_filter(
    user: "FFAdminUser", permission_key: str = None, allow_admin: bool = True
) -> Q:
    base_filter = Q(userpermission__user=user)
    permission_filter = Q(userpermission__admin=True) if allow_admin else Q()

    if permission_key:
        permission_filter = permission_filter | Q(
            userpermission__permissions__key=permission_key
        )

    return base_filter & permission_filter


def get_group_permission_filter(
    user: "FFAdminUser", permission_key: str = None, allow_admin: bool = True
) -> Q:
    base_filter = Q(grouppermission__group__users=user)
    permission_filter = Q(grouppermission__admin=True) if allow_admin else Q()

    if permission_key:
        permission_filter = permission_filter | Q(
            grouppermission__permissions__key=permission_key
        )
    return base_filter & permission_filter
