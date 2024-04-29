from typing import TYPE_CHECKING, List, Union

from django.db.models import Q, QuerySet

from environments.models import Environment
from organisations.models import Organisation, OrganisationRole
from projects.models import Project

from .rbac_wrapper import (
    get_permitted_environments_for_master_api_key_using_roles,
    get_permitted_projects_for_master_api_key_using_roles,
    get_role_permission_filter,
    is_master_api_key_object_admin,
    master_api_key_has_organisation_permission_using_roles,
)

if TYPE_CHECKING:
    from api_keys.models import MasterAPIKey
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


def is_master_api_key_project_admin(
    master_api_key: "MasterAPIKey", project: Project
) -> bool:
    if master_api_key.is_admin:
        return master_api_key.organisation_id == project.organisation_id
    return is_master_api_key_object_admin(master_api_key, project)


def is_master_api_key_environment_admin(
    master_api_key: "MasterAPIKey", environment: Environment
) -> bool:
    if master_api_key.is_admin:
        return master_api_key.organisation_id == environment.project.organisation_id
    return is_master_api_key_project_admin(
        master_api_key, environment.project
    ) or is_master_api_key_object_admin(master_api_key, environment)


def get_permitted_projects_for_user(
    user: "FFAdminUser", permission_key: str, tag_ids: List[int] = None
) -> QuerySet[Project]:
    """
    Get all projects that the user has the given permissions for.

    Rules:
        - User has the required permissions directly (UserProjectPermission)
        - User is in a UserPermissionGroup that has required permissions (UserPermissionGroupProjectPermissions)
        - User is an admin for the organisation the project belongs to
        - User has a role attached with the required permissions(if rbac is enabled)
        - User is in a UserPermissionGroup that has a role attached with the required permissions
    NOTE:
        - If `tag_ids` is None, tags filter will not be applied
        - If `tag_ids` is an empty list, only project with no tags will be returned
        - If `tag_ids` is a list of tag IDs, only project with one of those tags will
        be returned
    """
    base_filter = get_base_permission_filter(
        user, Project, permission_key, tag_ids=tag_ids
    )

    organisation_filter = Q(
        organisation__userorganisation__user=user,
        organisation__userorganisation__role=OrganisationRole.ADMIN.name,
    )
    filter_ = base_filter | organisation_filter
    return Project.objects.filter(filter_).distinct()


def get_permitted_projects_for_master_api_key(
    master_api_key: "MasterAPIKey", permission_key: str, tag_ids: List[int] = None
) -> QuerySet[Project]:
    if master_api_key.is_admin:
        return Project.objects.filter(organisation_id=master_api_key.organisation_id)

    return get_permitted_projects_for_master_api_key_using_roles(
        master_api_key, permission_key, tag_ids
    )


def get_permitted_environments_for_user(
    user: "FFAdminUser",
    project: Project,
    permission_key: str,
    tag_ids: List[int] = None,
    prefetch_metadata: bool = False,
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
    NOTE:
        - If `tag_ids` is None, tags filter will not be applied
        - If `tag_ids` is an empty list, only environments with no tags will be returned
        - If `tag_ids` is a list of tag IDs, only environments with one of those tags will
        be returned
    """

    if is_user_project_admin(user, project):
        queryset = project.environments.all()
        if prefetch_metadata:
            return queryset.prefetch_related("metadata")
        return queryset

    base_filter = get_base_permission_filter(
        user, Environment, permission_key, tag_ids=tag_ids
    )
    filter_ = base_filter & Q(project=project)

    queryset = Environment.objects.filter(filter_)
    if prefetch_metadata:
        queryset = queryset.prefetch_related("metadata")

    # Description is defered due to Oracle support where a
    # query can't have a where clause if description is in
    # the select parameters. This leads to an N+1 query for
    # lists of environments when description is included, as
    # each environment object re-queries the DB seperately.
    return queryset.distinct().defer("description")


def get_permitted_environments_for_master_api_key(
    master_api_key: "MasterAPIKey",
    project: Project,
    permission_key: str,
    tag_ids: List[int] = None,
    prefetch_metadata: bool = False,
) -> QuerySet[Environment]:
    if is_master_api_key_project_admin(master_api_key, project):
        queryset = project.environments.all()
    else:
        queryset = get_permitted_environments_for_master_api_key_using_roles(
            master_api_key, project, permission_key, tag_ids
        )

    if prefetch_metadata:
        queryset = queryset.prefetch_related("metadata")

    return queryset


def user_has_organisation_permission(
    user: "FFAdminUser", organisation: Organisation, permission_key: str
) -> bool:
    if is_user_organisation_admin(user, organisation):
        return True

    # NOTE: since we store organisation admin slightly differently
    # compared to project and environment `get_base_permission_filter`
    # with allow_admin=True will not work for organisation
    base_filter = get_base_permission_filter(
        user, Organisation, permission_key, allow_admin=False
    )
    filter_ = base_filter & Q(id=organisation.id)

    return Organisation.objects.filter(filter_).exists()


def master_api_key_has_organisation_permission(
    master_api_key: "MasterAPIKey", organisation: Organisation, permission_key: str
) -> bool:
    if master_api_key.is_admin:
        return master_api_key.organisation == organisation

    return master_api_key_has_organisation_permission_using_roles(
        master_api_key, organisation, permission_key
    )


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
    tag_ids=None,
) -> Q:
    user_filter = get_user_permission_filter(user, permission_key, allow_admin)
    group_filter = get_group_permission_filter(user, permission_key, allow_admin)

    role_filter = get_role_permission_filter(
        user, for_model, permission_key, allow_admin, tag_ids
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
