from core.apps import BaseAppConfig


class FeatureHealthConfig(BaseAppConfig):
    name = "features.feature_health"
    default = True

    def ready(self):
        from features.feature_health.tasks import (  # noqa
            send_feature_health_event,
        )

        return super().ready()
