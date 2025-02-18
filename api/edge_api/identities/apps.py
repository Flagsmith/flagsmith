from django.apps import AppConfig


class EdgeAPIIdentitiesAppConfig(AppConfig):
    name = "edge_api.identities"

    def ready(self):  # type: ignore[no-untyped-def]
        from . import tasks  # noqa
