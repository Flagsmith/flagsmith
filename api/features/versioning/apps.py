from django.apps import AppConfig


class FeatureVersioningAppConfig(AppConfig):
    label = "feature_versioning"
    name = "features.versioning"

    def ready(self):  # type: ignore[no-untyped-def]
        from . import receivers  # noqa
        from . import signals  # noqa
