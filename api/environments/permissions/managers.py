from django.db import models

from permissions.models import ENVIRONMENT_PERMISSION_TYPE


class EnvironmentPermissionManager(models.Manager):  # type: ignore[type-arg]
    def get_queryset(self):  # type: ignore[no-untyped-def]
        return (
            super(EnvironmentPermissionManager, self)
            .get_queryset()
            .filter(type=ENVIRONMENT_PERMISSION_TYPE)
        )
