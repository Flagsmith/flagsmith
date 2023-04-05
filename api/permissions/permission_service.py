from typing import Iterable, Set, Union

from django.db.models import Q

from environments.models import Environment
from organisations.models import Organisation, OrganisationRole
from projects.models import Project


def is_user_organisation_admin(user, organisation: Organisation) -> bool:
    user_organisation = user.get_user_organisation(organisation)
    if user_organisation is not None:
        if user_organisation.role == OrganisationRole.ADMIN.name:
            return True
    return False


def is_user_project_admin(user, project) -> bool:
    if is_user_organisation_admin(user, project.organisation):
        return True
    return _is_user_object_admin(user, project)


def get_permitted_projects_for_user(user, permission_key: str) -> Iterable[Project]:
    """
    Get all projects that the user has the given permissions for.

    Rules:
        - User has the required permissions directly (UserProjectPermission)
        - User is in a UserPermissionGroup that has required permissions (UserPermissionGroupProjectPermissions)
        - User is an admin for the organisation the project belongs to
        - User has a role attached with the required permissions
        - User is in a UserPermissionGroup has a role attached with the required permissions
    """
    base_query = _get_base_query(user, permission_key)

    organisation_query = Q(
        organisation__userorganisation__user=user,
        organisation__userorganisation__role=OrganisationRole.ADMIN.name,
    )
    query = base_query | organisation_query
    return Project.objects.filter(query).distinct()


def get_permitted_environments_for_user(
    user, permission_key: str, project: Project
) -> Iterable[Environment]:
    """
    Get all environments that the user has the given permissions for.

    Rules:
        - User has the required permissions directly (UserEnvironmentPermission)
        - User is in a UserPermissionGroup that has required permissions (UserPermissionGroupEnvironmentPermissions)
        - User is an admin for the project the environment belongs to
        - User is an admin for the organisation the environment belongs to
        - User has a role attached with the required permissions
        - User is in a UserPermissionGroup has a role attached with the required permissions
    """

    if is_user_project_admin(user, project):
        return project.environments.all()

    query = _get_base_query(user, permission_key)
    query = query & Q(project=project)

    return Environment.objects.filter(query).distinct().defer("description")


def user_has_organisation_permission(user, organisation, permission_key: str) -> bool:
    if is_user_organisation_admin(user, organisation):
        return True
    user_query = _user_query(user, permission_key, allow_admin=False)
    group_query = _group_query(user, permission_key, allow_admin=False)

    role_query = Q(
        Q(role__userrole__user=user) | Q(role__grouprole__group__users=user)
    ) & Q(role__rolepermission__permissions__key=permission_key)

    query = user_query | group_query | role_query

    return Organisation.objects.filter(query).exists()


def get_organisation_permission_keys_for_user(
    user, organisation: Organisation
) -> Set[str]:
    user_permission_keys = (
        organisation.userpermissions.filter(user=user)
        .values_list("permissions__key", flat=True)
        .exclude(permissions__key__isnull=True)
    )

    group_permission_keys = (
        organisation.grouppermissions.filter(group__users=user)
        .values_list("permissions__key", flat=True)
        .exclude(permissions__key__isnull=True)
    )

    role_permission_keys = (
        organisation.roles.filter(
            Q(rolepermission__role__userrole__user=user)
            | Q(rolepermission__role__grouprole__group__users=user)
        )
        .values_list("rolepermission__permissions__key", flat=True)
        .exclude(rolepermission__permissions__key__isnull=True)
    )

    all_permission_keys = (
        set(user_permission_keys)
        | set(group_permission_keys)
        | set(role_permission_keys)
    )

    return all_permission_keys


def is_user_environment_admin(user, environment) -> bool:
    return (
        is_user_organisation_admin(user, environment.project.organisation)
        or is_user_project_admin(user, environment.project)
        or _is_user_object_admin(user, environment)
    )


def _is_user_object_admin(user, object_: Union[Project | Environment]) -> bool:
    query = _get_base_query(user)
    query = query & Q(id=object_.id)
    return type(object_).objects.filter(query).exists()


def _get_base_query(user, permission_key: str = None, allow_admin=True) -> Q:
    """
    Get all objects of the given model that the user has the given permissions for.
    Rules:
        - User has the required permissions directly (UserObjectPermission)
        - User is in a UserPermissionGroup that has required permissions (UserPermissionGroupObjectPermissions)
        - User is an admin for the project or organisation the object belongs to
        - User has a role attached with the required permissions
        - User is in a UserPermissionGroup has a role attached with the required permissions
    """
    user_query = _user_query(user, permission_key, allow_admin)
    group_query = _group_query(user, permission_key, allow_admin)
    role_query = _role_query(user, permission_key, allow_admin)

    query = user_query | group_query | role_query
    return query


def _user_query(user, permission_key=None, allow_admin=True) -> Q:
    base_query = Q(userpermission__user=user)
    permission_query = Q(userpermission__admin=True) if allow_admin else Q()

    if permission_key:
        permission_query = permission_query | Q(
            userpermission__permissions__key=permission_key
        )

    return base_query & permission_query


def _group_query(user, permission_key: str = None, allow_admin=True) -> Q:
    base_query = Q(grouppermission__group__users=user)
    permission_query = Q(grouppermission__admin=True) if allow_admin else Q()
    if permission_key:
        permission_query = permission_query | Q(
            grouppermission__permissions__key=permission_key
        )
    return base_query & permission_query


def _role_query(user, permission_key: str = None, allow_admin=True) -> Q:
    base_query = Q(rolepermission__role__userrole__user=user) | Q(
        rolepermission__role__grouprole__group__users=user
    )
    permission_query = Q(rolepermission__admin=True) if allow_admin else Q()
    if permission_key:
        permission_query = permission_query | Q(
            rolepermission__permissions__key=permission_key
        )
    return base_query & permission_query
