from django.apps import AppConfig


class AuditConfig(AppConfig):
    default = True
    name = "audit"

    def ready(self):
        from . import signals  # noqa
