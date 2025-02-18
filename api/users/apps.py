from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "users"

    def ready(self):  # type: ignore[no-untyped-def]
        from . import signals  # noqa
