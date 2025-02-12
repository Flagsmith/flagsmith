from core.apps import BaseAppConfig


class FeatureHealthConfig(BaseAppConfig):
    name = "features.feature_health"
    default = True

    def ready(self):
        from features.feature_health.tasks import (  # noqa
            update_feature_unhealthy_tag,
        )

        return super().ready()
