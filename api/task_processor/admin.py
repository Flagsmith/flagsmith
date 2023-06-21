from django.contrib import admin

from task_processor.models import (
    RecurringTask,
    RecurringTaskRun,
    Task,
    TaskRun,
)


class TaskRunInline(admin.StackedInline):
    model = TaskRun
    extra = 0
    show_change_link = False


class RecurringTaskRunInline(admin.StackedInline):
    model = RecurringTaskRun
    extra = 0
    show_change_link = False


@admin.register(RecurringTask)
class RecurringTaskAdmin(admin.ModelAdmin):
    inlines = (RecurringTaskRunInline,)
    list_display = ("uuid", "task_identifier", "run_every", "last_run_status")
    readonly_fields = ("args", "kwargs")

    def last_run_status(self, instance: Task) -> str:
        return instance.task_runs.order_by("-started_at").first().result
