from __future__ import unicode_literals

from django.apps import AppConfig


class AuditConfig(AppConfig):
    name = "audit"

    def ready(self):  # type: ignore[no-untyped-def]
        from . import signals  # noqa
