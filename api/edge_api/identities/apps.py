from django.apps import AppConfig


class TaskProcessorAppConfig(AppConfig):
    name = "edge_api.identities"

    def ready(self):
        from . import tasks  # noqa
