from django.db import models

PROJECT_PERMISSION_TYPE = "PROJECT"
ENVIRONMENT_PERMISSION_TYPE = "ENVIRONMENT"
ORGANISATION_PERMISSION_TYPE = "ORGANISATION"

PERMISSION_TYPES = (
    (PROJECT_PERMISSION_TYPE, "Project"),
    (ENVIRONMENT_PERMISSION_TYPE, "Environment"),
    (ORGANISATION_PERMISSION_TYPE, "Organisation"),
)


class PermissionModel(models.Model):
    key = models.CharField(max_length=100, primary_key=True)
    description = models.TextField()
    type = models.CharField(max_length=100, choices=PERMISSION_TYPES, null=True)


class AbstractBasePermissionModel(models.Model):
    class Meta:
        abstract = True

    permissions = models.ManyToManyField(PermissionModel, blank=True)

    def add_permission(self, permission_key: str):  # type: ignore[no-untyped-def]
        permission = PermissionModel.objects.get(key=permission_key)
        self.permissions.add(permission)

    def set_permissions(self, permission_keys: list):  # type: ignore[no-untyped-def,type-arg]
        permissions = []
        for permission_key in permission_keys:
            permissions.append(PermissionModel.objects.get(key=permission_key))
        self.permissions.set(permissions)
