import atexit
import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class AppAnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_analytics"

    def ready(self) -> None:
        atexit.register(flush_analytics_caches)


def flush_analytics_caches() -> None:
    try:
        from app_analytics.services import api_usage_cache
        from app_analytics.views import feature_evaluation_cache

        api_usage_cache.flush_on_shutdown()
        feature_evaluation_cache.flush_on_shutdown()
    except Exception:
        logger.exception("Failed to flush analytics caches during shutdown")
