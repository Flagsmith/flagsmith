from typing import List, Union

from django.conf import settings
from django.db.models import Q, QuerySet

from api_keys.models import MasterAPIKey
from environments.models import Environment
from organisations.models import Organisation
from projects.models import Project

if settings.IS_RBAC_INSTALLED:
    from rbac.permission_service import get_role_permission_filter
    from rbac.permissions_calculator import (
        RolePermissionData,
        get_roles_permission_data_for_environment,
        get_roles_permission_data_for_organisation,
        get_roles_permission_data_for_project,
    )
else:
    RolePermissionData = []

    def get_roles_permission_data_for_organisation(*args, **kwargs):
        return []

    def get_roles_permission_data_for_project(*args, **kwargs):
        return []

    def get_roles_permission_data_for_environment(*args, **kwargs):
        return []

    def get_role_permission_filter(*args, **kwargs) -> Q:
        return Q()


def is_master_api_key_object_admin(
    master_api_key: "MasterAPIKey", object_: Union[Project, Environment]
) -> bool:
    if not settings.IS_RBAC_INSTALLED:
        return False

    ModelClass = type(object_)

    base_filter = get_role_permission_filter(master_api_key, ModelClass)
    filter_ = base_filter & Q(id=object_.id)
    return ModelClass.objects.filter(filter_).exists()


def get_permitted_projects_for_master_api_key_using_roles(
    master_api_key: "MasterAPIKey", permission_key: str, tag_ids=None
) -> QuerySet[Project]:
    if not settings.IS_RBAC_INSTALLED:
        return Project.objects.none()

    filter_ = get_role_permission_filter(
        master_api_key, Project, permission_key, tag_ids=tag_ids
    )
    return Project.objects.filter(filter_).distinct()


def get_permitted_environments_for_master_api_key_using_roles(
    master_api_key: "MasterAPIKey",
    project: Project,
    permission_key: str,
    tag_ids: List[int] = None,
) -> QuerySet[Environment]:
    if not settings.IS_RBAC_INSTALLED:
        return Environment.objects.none()

    base_filter = get_role_permission_filter(
        master_api_key, Environment, permission_key, tag_ids=tag_ids
    )

    filter_ = base_filter & Q(project=project)

    return Environment.objects.filter(filter_).distinct().defer("description")


def master_api_key_has_organisation_permission_using_roles(
    master_api_key: "MasterAPIKey", organisation: Organisation, permission_key: str
) -> bool:
    if not settings.IS_RBAC_INSTALLED:
        return False

    base_filter = get_role_permission_filter(
        master_api_key, Organisation, permission_key
    )
    filter_ = base_filter & Q(id=organisation.id)

    return Organisation.objects.filter(filter_).exists()
