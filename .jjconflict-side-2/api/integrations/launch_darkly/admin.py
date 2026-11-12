from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils import timezone

from integrations.launch_darkly.models import LaunchDarklyImportRequest


@admin.register(LaunchDarklyImportRequest)
class LaunchDarklyImportRequestAdmin(admin.ModelAdmin[LaunchDarklyImportRequest]):
    actions = ["mark_as_failure"]
    date_hierarchy = "created_at"
    exclude = ("ld_token",)
    list_display = (
        "id",
        "project",
        "ld_project_key",
        "created_by",
        "created_at",
        "completed_at",
        "result",
    )
    list_select_related = ("project", "created_by")
    readonly_fields = (
        "project",
        "created_by",
        "created_at",
        "updated_at",
        "completed_at",
        "ld_project_key",
        "status",
    )
    search_fields = (
        "project__name",
        "ld_project_key",
        "created_by__email",
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    @admin.display(description="Result")
    def result(self, obj: LaunchDarklyImportRequest) -> str:
        return obj.status.get("result") or "pending"

    @admin.action(description="Mark selected imports as failed")
    def mark_as_failure(
        self,
        request: HttpRequest,
        queryset: QuerySet[LaunchDarklyImportRequest],
    ) -> None:
        now = timezone.now()
        marked = 0
        skipped = 0
        for import_request in queryset:
            if import_request.status.get("result"):
                skipped += 1
                continue
            import_request.status = {**import_request.status, "result": "failure"}
            if not import_request.completed_at:
                import_request.completed_at = now
            import_request.save()
            marked += 1
        self.message_user(
            request,
            f"Marked {marked} import(s) as failed; "
            f"skipped {skipped} already-resolved import(s).",
            messages.SUCCESS,
        )
