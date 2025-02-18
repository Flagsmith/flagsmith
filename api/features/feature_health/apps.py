from core.apps import BaseAppConfig


class FeatureHealthConfig(BaseAppConfig):
    name = "features.feature_health"
    default = True

    def ready(self):  # type: ignore[no-untyped-def]
        from features.feature_health.tasks import (  # noqa
            update_feature_unhealthy_tag,
        )

        return super().ready()  # type: ignore[no-untyped-call]
