from django.contrib import admin
from django.db.models import Count, Q

from task_processor.models import Task, TaskResult, TaskRun


class TaskRunInline(admin.StackedInline):
    model = TaskRun
    extra = 0
    show_change_link = False


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    inlines = (TaskRunInline,)
    list_display = (
        "uuid",
        "task_identifier",
        "scheduled_for",
        "num_failures",
        "completed",
    )
    readonly_fields = ("args", "kwargs")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                successful_task_runs=Count(
                    "task_runs", Q(task_runs__result=TaskResult.SUCCESS)
                )
            )
        )

    def completed(self, instance: Task) -> bool:
        return instance.successful_task_runs == 1
