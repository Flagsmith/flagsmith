from django.apps import AppConfig
from django.conf import settings
from health_check.plugins import plugin_dir


class TaskProcessorAppConfig(AppConfig):
    name = "task_processor"

    def ready(self):
        from . import tasks  # noqa

        if not settings.RUN_TASKS_SYNCHRONOUSLY:
            from .health import TaskProcessorHealthCheckBackend

            plugin_dir.register(TaskProcessorHealthCheckBackend)
