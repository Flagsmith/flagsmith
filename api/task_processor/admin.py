from typing import Optional

from django.contrib import admin

from task_processor.models import RecurringTask


@admin.register(RecurringTask)
class RecurringTaskAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "task_identifier",
        "run_every",
        "last_run_status",
        "is_locked",
    )
    readonly_fields = ("args", "kwargs")

    def last_run_status(self, instance: RecurringTask) -> Optional[str]:
        if last_run := instance.task_runs.order_by("-started_at").first():
            return last_run.result
        return None
