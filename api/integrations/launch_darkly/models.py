from typing import TYPE_CHECKING, Literal, Optional, TypedDict

from django.db import models
from typing_extensions import NotRequired

from audit.related_object_type import RelatedObjectType
from core.models import abstract_base_auditable_model_factory
from projects.models import Project

if TYPE_CHECKING:
    from users.models import FFAdminUser


class LaunchDarklyImportStatus(TypedDict):
    requested_environment_count: int
    requested_flag_count: int
    result: NotRequired[Literal["success", "failure"]]
    error_messages: list[str]


class LaunchDarklyImportRequest(
    abstract_base_auditable_model_factory(),  # type: ignore[misc]
):
    history_record_class_path = (
        "integrations.launch_darkly.models.HistoricalLaunchDarklyImportRequest"
    )
    related_object_type = RelatedObjectType.IMPORT_REQUEST

    created_by = models.ForeignKey("users.FFAdminUser", on_delete=models.CASCADE)  # type: ignore[var-annotated]
    project = models.ForeignKey(Project, on_delete=models.CASCADE)  # type: ignore[var-annotated]

    created_at = models.DateTimeField(auto_now_add=True)  # type: ignore[var-annotated]
    updated_at = models.DateTimeField(auto_now=True)  # type: ignore[var-annotated]
    completed_at = models.DateTimeField(null=True, blank=True)  # type: ignore[var-annotated]

    ld_project_key = models.CharField(max_length=2000)  # type: ignore[var-annotated]
    ld_token = models.CharField(max_length=2000)  # type: ignore[var-annotated]

    status: LaunchDarklyImportStatus = models.JSONField()  # type: ignore[assignment]

    def get_create_log_message(self, _) -> str:  # type: ignore[no-untyped-def]
        return "New LaunchDarkly import requested"

    def get_update_log_message(self, _) -> Optional[str]:  # type: ignore[no-untyped-def]
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

    def get_audit_log_author(self, history_instance) -> "FFAdminUser":  # type: ignore[no-untyped-def]
        return self.created_by  # type: ignore[no-any-return]

    def _get_project(self) -> Project:
        return self.project  # type: ignore[no-any-return]

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name="unique_project_ld_project_key_status_result_null",
                fields=["project", "ld_project_key"],
                condition=models.Q(status__result__isnull=True),
            )
        ]
