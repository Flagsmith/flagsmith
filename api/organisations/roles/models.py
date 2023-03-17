from django.db import models

from organisations.models import Organisation
from permissions.models import AbstractBasePermissionModel


class Role(AbstractBasePermissionModel):
    name = models.CharField(max_length=2000)
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="roles"
    )
