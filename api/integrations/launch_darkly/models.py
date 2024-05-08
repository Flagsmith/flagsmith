from typing import TYPE_CHECKING, Literal, Optional, TypedDict

from core.models import abstract_base_auditable_model_factory
from django.db import models
from typing_extensions import NotRequired

from audit.related_object_type import RelatedObjectType
from projects.models import Project

if TYPE_CHECKING:
    from users.models import FFAdminUser


class LaunchDarklyImportStatus(TypedDict):
    requested_environment_count: int
    requested_flag_count: int
    result: NotRequired[Literal["success", "failure"]]
    error_messages: list[str]


class LaunchDarklyImportRequest(
    abstract_base_auditable_model_factory(),
):
    history_record_class_path = "features.models.HistoricalLaunchDarklyImportRequest"
    related_object_type = RelatedObjectType.IMPORT_REQUEST

    created_by = models.ForeignKey("users.FFAdminUser", on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    ld_project_key = models.CharField(max_length=2000)
    ld_token = models.CharField(max_length=2000)

    status: LaunchDarklyImportStatus = models.JSONField()

    def get_create_log_message(self, _) -> str:
        return "New LaunchDarkly import requested"

    def get_update_log_message(self, _) -> Optional[str]:
        if not self.completed_at:
            return None
        if self.status.get("result") == "success":
            return "LaunchDarkly import completed successfully"
        if error_messages := self.status.get("error_messages"):
            if len(error_messages) > 0:
                return "LaunchDarkly import failed with errors:\n" + "\n".join(
                    "- " + error_message for error_message in error_messages
                )
        return "LaunchDarkly import failed"

    def get_audit_log_author(self) -> "FFAdminUser":
        return self.created_by

    def _get_project(self) -> Project:
        return self.project

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name="unique_project_ld_project_key_status_result_null",
                fields=["project", "ld_project_key"],
                condition=models.Q(status__result__isnull=True),
            )
        ]
