from typing import TYPE_CHECKING, Union

from django.db.models import Q, QuerySet

from environments.models import Environment
from organisations.models import Organisation, OrganisationRole
from projects.models import Project

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
        - User has a role attached with the required permissions
        - User is in a UserPermissionGroup that has a role attached with the required permissions
    """
    base_query = _get_base_permission_query(user, permission_key)

    organisation_query = Q(
        organisation__userorganisation__user=user,
        organisation__userorganisation__role=OrganisationRole.ADMIN.name,
    )
    query = base_query | organisation_query
    return Project.objects.filter(query).distinct()


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
        - User has a role attached with the required permissions
        - User is in a UserPermissionGroup that has a role attached with the required permissions
    """

    if is_user_project_admin(user, project):
        return project.environments.all()

    query = _get_base_permission_query(user, permission_key)
    query = query & Q(project=project)

    return Environment.objects.filter(query).distinct().defer("description")


def user_has_organisation_permission(
    user: "FFAdminUser", organisation: Organisation, permission_key: str
) -> bool:
    if is_user_organisation_admin(user, organisation):
        return True

    user_query = _user_permission_query(user, permission_key, allow_admin=False)
    group_query = _group_permission_query(user, permission_key, allow_admin=False)

    role_query = Q(
        Q(role__userrole__user=user) | Q(role__grouprole__group__users=user)
    ) & Q(role__org_role_permission__permissions__key=permission_key)

    query = user_query | group_query | role_query

    return Organisation.objects.filter(query).exists()


def _is_user_object_admin(
    user: "FFAdminUser", object_: Union[Project | Environment]
) -> bool:
    query = _get_base_permission_query(user)
    query = query & Q(id=object_.id)
    return type(object_).objects.filter(query).exists()


def _get_base_permission_query(
    user: "FFAdminUser", permission_key: str = None, allow_admin: bool = True
) -> Q:
    user_query = _user_permission_query(user, permission_key, allow_admin)
    group_query = _group_permission_query(user, permission_key, allow_admin)
    role_query = _role_permission_query(user, permission_key, allow_admin)

    query = user_query | group_query | role_query
    return query


def _user_permission_query(
    user: "FFAdminUser", permission_key: str = None, allow_admin: bool = True
) -> Q:
    base_query = Q(userpermission__user=user)
    permission_query = Q(userpermission__admin=True) if allow_admin else Q()

    if permission_key:
        permission_query = permission_query | Q(
            userpermission__permissions__key=permission_key
        )

    return base_query & permission_query


def _group_permission_query(
    user: "FFAdminUser", permission_key: str = None, allow_admin: bool = True
) -> Q:
    base_query = Q(grouppermission__group__users=user)
    permission_query = Q(grouppermission__admin=True) if allow_admin else Q()

    if permission_key:
        permission_query = permission_query | Q(
            grouppermission__permissions__key=permission_key
        )
    return base_query & permission_query


def _role_permission_query(
    user: "FFAdminUser", permission_key: str = None, allow_admin: bool = True
) -> Q:
    base_query = Q(rolepermission__role__userrole__user=user) | Q(
        rolepermission__role__grouprole__group__users=user
    )
    permission_query = Q(rolepermission__admin=True) if allow_admin else Q()
    if permission_key:
        permission_query = permission_query | Q(
            rolepermission__permissions__key=permission_key
        )
    return base_query & permission_query
