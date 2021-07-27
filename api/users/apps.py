from django.apps import AppConfig
from django.db.models.signals import post_migrate

from .signals import warn_insecure


class UsersConfig(AppConfig):
    name = "users"

    def ready(self):
        post_migrate.connect(warn_insecure, self)
