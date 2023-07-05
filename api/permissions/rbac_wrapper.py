from django.conf import settings
from django.db.models import Q

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
