from core.models import (
    SoftDeleteObject,
    abstract_base_auditable_model_factory,
)
from django.db import models

from audit.related_object_type import RelatedObjectType


PROJECT_PERMISSION_TYPE = "PROJECT"
ENVIRONMENT_PERMISSION_TYPE = "ENVIRONMENT"
ORGANISATION_PERMISSION_TYPE = "ORGANISATION"

PERMISSION_TYPES = (
    (PROJECT_PERMISSION_TYPE, "Project"),
    (ENVIRONMENT_PERMISSION_TYPE, "Environment"),
    (ORGANISATION_PERMISSION_TYPE, "Organisation"),
)


# effectively read-only - not audited
class PermissionModel(models.Model):
    key = models.CharField(max_length=100, primary_key=True)
    description = models.TextField()
    type = models.CharField(max_length=100, choices=PERMISSION_TYPES, null=True)


class AbstractBasePermissionModel(
    SoftDeleteObject,
    abstract_base_auditable_model_factory(
        audited_m2m_fields=("permissions",),
        audit_create=True,
        audit_update=True,
        audit_delete=True,
    ),
):
    related_object_type = RelatedObjectType.GRANT

    class Meta:
        abstract = True

    permissions = models.ManyToManyField(PermissionModel, blank=True)

    def add_permission(self, permission_key: str):
        permission = PermissionModel.objects.get(key=permission_key)
        self.permissions.add(permission)

    def set_permissions(self, permission_keys: list):
        permissions = []
        for permission_key in permission_keys:
            permissions.append(PermissionModel.objects.get(key=permission_key))
        self.permissions.set(permissions)
