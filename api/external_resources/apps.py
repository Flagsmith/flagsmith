from django.apps import AppConfig


class ExternalResourcesConfig(AppConfig):
    name = "external_resources"

    def ready(self):
        # noinspection PyUnresolvedReferences
        import external_resources.signals  # noqa
