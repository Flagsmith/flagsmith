from django.conf import settings

from app_analytics.cache import APIUsageCache
from app_analytics.models import Resource
from app_analytics.tasks import track_request
from app_analytics.types import Labels

api_usage_cache = APIUsageCache()


def track_usage_by_resource_host_and_environment(
    resource: Resource | None,
    host: str,
    environment_key: str,
    labels: Labels,
) -> None:
    if resource and resource.is_tracked:
        if settings.USE_CACHE_FOR_USAGE_DATA:
            api_usage_cache.track_request(
                resource=resource,
                host=host,
                environment_key=environment_key,
                labels=labels,
            )
        else:
            track_request.run_in_thread(
                kwargs={
                    "resource": resource.value,
                    "host": host,
                    "environment_key": environment_key,
                    "labels": labels,
                }
            )
