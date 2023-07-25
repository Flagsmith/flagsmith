from django.contrib import admin

from task_processor.models import (
    RecurringTask,
    RecurringTaskRun,
    Task,
    TaskRun,
)


@admin.register(RecurringTask)
class RecurringTaskAdmin(admin.ModelAdmin):
    list_display = ("uuid", "task_identifier", "run_every", "last_run_status", "is_locked")
    readonly_fields = ("args", "kwargs")

    def last_run_status(self, instance: RecurringTask) -> str:
        return instance.task_runs.order_by("-started_at").first().result
