from core.apps import BaseAppConfig


class UsersConfig(BaseAppConfig):
    default = True
    name = "users"

    def ready(self):
        super().ready()
        from . import signals  # noqa
