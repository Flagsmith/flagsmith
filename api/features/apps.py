from core.apps import BaseAppConfig


class FeaturesConfig(BaseAppConfig):
    default = True
    name = "features"

    def ready(self):
        super().ready()
        # noinspection PyUnresolvedReferences
        import features.signals  # noqa
