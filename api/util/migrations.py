from typing import List, Union

from django.db import models

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

PermissionModelType = Union[
    UserEnvironmentPermission,
    UserPermissionGroupEnvironmentPermission,
    UserProjectPermission,
    UserPermissionGroupProjectPermission,
    UserOrganisationPermission,
    UserPermissionGroupOrganisationPermission,
]


def merge_duplicate_permissions(
    PermissionModel: PermissionModelType, duplicate_for: List[str]
):
    # find all duplicate permissions
    duplicates = (
        PermissionModel.objects.values(*duplicate_for)
        .annotate(count=models.Count("id"))
        .filter(count__gt=1)
    ).values(*duplicate_for)

    for duplicate in duplicates:
        # find all duplicate permissions for a given user and project
        duplicate_permissions = PermissionModel.objects.filter(**duplicate)

        # let's move all the perms to the first object
        merged_permission = duplicate_permissions[0]
        for duplicate_permission in duplicate_permissions[1:]:
            if getattr(duplicate_permission, "admin", False):
                merged_permission.admin = True
                merged_permission.save()

            for permission in duplicate_permission.permissions.all():
                merged_permission.permissions.add(permission)

            # delete the duplicate permission
            duplicate_permission.delete()
