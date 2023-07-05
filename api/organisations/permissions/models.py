from __future__ import unicode_literals

from django.db import models

from organisations.managers import OrganisationPermissionManager
from organisations.models import Organisation
from permissions.models import AbstractBasePermissionModel, PermissionModel


class UserOrganisationPermission(AbstractBasePermissionModel):
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_query_name="userpermission",
    )
    user = models.ForeignKey("users.FFAdminUser", on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "organisation"],
                name="unique_user_organisation_permission",
            )
        ]


class UserPermissionGroupOrganisationPermission(AbstractBasePermissionModel):
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_query_name="grouppermission",
    )
    group = models.ForeignKey("users.UserPermissionGroup", on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["group", "organisation"],
                name="unique_group_organisation_permission",
            )
        ]


class OrganisationPermissionModel(PermissionModel):
    class Meta:
        proxy = True

    objects = OrganisationPermissionManager()
