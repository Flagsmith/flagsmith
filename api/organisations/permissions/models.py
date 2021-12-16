from __future__ import unicode_literals

from django.db import models

from organisations.managers import OrganisationPermissionManager
from organisations.models import Organisation
from permissions.models import AbstractBasePermissionModel, PermissionModel


class UserOrganisationPermission(AbstractBasePermissionModel):
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    user = models.ForeignKey("users.FFAdminUser", on_delete=models.CASCADE)


class UserPermissionGroupOrganisationPermission(AbstractBasePermissionModel):
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    group = models.ForeignKey("users.UserPermissionGroup", on_delete=models.CASCADE)


class OrganisationPermissionModel(PermissionModel):
    class Meta:
        proxy = True

    objects = OrganisationPermissionManager()
