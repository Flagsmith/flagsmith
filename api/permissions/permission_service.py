from typing import Iterable

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


def is_user_project_admin(user, project, allow_org_admin: bool = True) -> bool:
    if allow_org_admin and is_user_organisation_admin(user, project.organisation):
        return True

    user_query = Q(userpermission__user=user, userpermission__admin=True)
    group_query = Q(grouppermission__group__users=user, grouppermission__admin=True)

    user_role_query = Q(
        rolepermission__role__userrole__user=user, rolepermission__admin=True
    )
    groups_role_query = Q(
        rolepermission__role__grouprole__group__users=user,
        rolepermission__admin=True,
    )

    query = user_role_query | groups_role_query | user_query | group_query

    query = query & Q(id=project.id)

    return Project.objects.filter(query).exists()


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
    user_query = Q(userpermission__user=user) & (
        Q(userpermission__permissions__key=permission_key)
        | Q(userpermission__admin=True)
    )
    group_query = Q(grouppermission__group__users=user) & (
        Q(grouppermission__permissions__key=permission_key)
        | Q(grouppermission__admin=True)
    )
    organisation_query = Q(
        organisation__userorganisation__user=user,
        organisation__userorganisation__role=OrganisationRole.ADMIN.name,
    )
    user_role_query = Q(rolepermission__role__userrole__user=user) & (
        Q(rolepermission__admin=True)
        | Q(rolepermission__permissions__key=permission_key)
    )
    group_role_query = Q(rolepermission__role__grouprole__group__users=user) & (
        Q(rolepermission__admin=True)
        | Q(rolepermission__permissions__key=permission_key)
    )

    query = (
        user_query
        | group_query
        | organisation_query
        | user_role_query
        | group_role_query
    )

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

    user_query = Q(userpermission__user=user) & (
        Q(userpermission__permissions__key=permission_key)
        | Q(userpermission__admin=True)
    )
    group_query = Q(grouppermission__group__users=user) & (
        Q(grouppermission__permissions__key=permission_key)
        | Q(grouppermission__admin=True)
    )
    role_permission = Q(
        Q(rolepermission__role__userrole__user=user)
        | Q(rolepermission__role__grouprole__group__users=user)
    ) & (
        Q(rolepermission__permissions__key=permission_key)
        | Q(rolepermission__admin=True)
    )

    return (
        Environment.objects.filter(
            Q(project=project) & Q(user_query | group_query | role_permission)
        )
        .distinct()
        .defer("description")
    )


def user_has_organisation_permission(user, organisation, permission_key: str) -> bool:
    if is_user_organisation_admin(user, organisation):
        return True

    user_query = Q(userpermission__user=user) & (
        Q(userpermission__permissions__key=permission_key)
    )
    group_query = Q(grouppermission__group__users=user) & (
        Q(grouppermission__permissions__key=permission_key)
    )
    user_role_query = Q(roles__userrole__user=user) & (
        Q(roles__permissions__key=permission_key)
    )
    groups_role_query = Q(roles__grouprole__group__users=user) & (
        Q(roles__permissions__key=permission_key)
    )

    query = user_query | group_query | user_role_query | groups_role_query

    return Organisation.objects.filter(query).exists()


def get_organisation_permission_keys_for_user(
    user, organisation: Organisation
) -> Iterable[str]:
    """
    Get all permissions that the user has for the given organisation.

    Rules:
        - User has the required permissions directly (UserOrganisationPermission)
        - User is in a UserPermissionGroup that has required permissions (UserPermissionGroupOrganisationPermissions)
        - User is an admin for the organisation
        - User has a role attached with the required permissions
        - User is in a UserPermissionGroup has a role attached with the required permissions
    """
    if is_user_organisation_admin(user, organisation):
        return organisation.permissions.all().values_list("key", flat=True)

    user_query = Q(userpermission__user=user)
    group_query = Q(grouppermission__group__users=user)
    user_role_query = Q(rolepermission__role__userrole__user=user)
    groups_role_query = Q(rolepermission__role__grouprole__group__users=user)

    query = user_query | group_query | user_role_query | groups_role_query

    return organisation.permissions.filter(query).values_list("key", flat=True)
