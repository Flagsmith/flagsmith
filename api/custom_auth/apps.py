from django.apps import AppConfig


class CustomAuthAppConfig(AppConfig):
    name = "custom_auth"

    def ready(self) -> None:
        from custom_auth import tasks  # noqa F401
