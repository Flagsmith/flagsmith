from __future__ import unicode_literals

from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = "api"

    def ready(self) -> None:
        # Import openapi extensions to register them with drf-spectacular
        from api import openapi  # noqa: F401
