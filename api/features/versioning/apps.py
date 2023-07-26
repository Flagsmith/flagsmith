from django.apps import AppConfig


class FeatureVersioningAppConfig(AppConfig):
    label = "feature_versioning"
    name = "features.versioning"

    def ready(self):
        from . import signals  # noqa
