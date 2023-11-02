from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypedDict

from core.models import abstract_base_auditable_model_factory
from django.db import models
from typing_extensions import NotRequired

from audit.related_object_type import RelatedObjectType
from projects.models import Project

if TYPE_CHECKING:  # pragma: no cover
    from users.models import FFAdminUser


class LaunchDarklyImportStatus(TypedDict):
    requested_environment_count: int
    requested_flag_count: int
    result: NotRequired[Literal["success", "failure"]]
    error_message: NotRequired[str]


class LaunchDarklyImportRequest(
    abstract_base_auditable_model_factory(RelatedObjectType.IMPORT_REQUEST),
):
    created_by = models.ForeignKey("users.FFAdminUser", on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    ld_project_key = models.CharField(max_length=2000)
    ld_token = models.CharField(max_length=2000)

    status: LaunchDarklyImportStatus = models.JSONField()

    def get_create_log_message(self, history_instance) -> str | None:
        return "New LaunchDarkly import requested"

    def get_update_log_message(self, history_instance, delta) -> str | None:
        if not self.completed_at:
            return None
        if self.status.get("result") == "success":
            return "LaunchDarkly import completed successfully"
        if error_message := self.status.get("error_message"):
            return f"LaunchDarkly import failed with error: {error_message}"
        return "LaunchDarkly import failed"

    def get_audit_log_author(self) -> FFAdminUser:
        return self.created_by

    def _get_project(self, delta=None) -> Project | None:
        return self.project

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name="unique_project_ld_project_key_status_result_null",
                fields=["project", "ld_project_key"],
                condition=models.Q(status__result__isnull=True),
            )
        ]
