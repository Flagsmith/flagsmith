from core.models import abstract_base_auditable_model_factory
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
    abstract_base_auditable_model_factory(
        RelatedObjectType.GRANT,
        audited_m2m_fields=["permissions"],
        audit_create=True,
        audit_update=True,
        audit_delete=True,
    ),
):
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

    def get_update_log_message(self, history_instance, delta) -> str | None:
        if not (message := super().get_update_log_message(history_instance, delta)):
            return message

        for change in delta.changes:
            if change.field == "permissions":
                old_keys = set(through["permissionmodel"] for through in change.old)
                new_keys = set(through["permissionmodel"] for through in change.new)
                for key in new_keys - old_keys:
                    message += f"; added {key}"
                for key in old_keys - new_keys:
                    message += f"; removed {key}"

        return message
