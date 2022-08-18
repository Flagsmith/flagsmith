from django.apps import AppConfig


class EdgeAPIIdentitiesAppConfig(AppConfig):
    name = "edge_api.identities"

    def ready(self):
        from . import tasks  # noqa
