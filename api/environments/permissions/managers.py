from django.db import models

from permissions.models import ENVIRONMENT_PERMISSION_TYPE


class EnvironmentPermissionManager(models.Manager):
    def get_queryset(self):
        return (
            super(EnvironmentPermissionManager, self)
            .get_queryset()
            .filter(type=ENVIRONMENT_PERMISSION_TYPE)
        )
