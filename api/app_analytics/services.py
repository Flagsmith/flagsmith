from datetime import datetime

from django.conf import settings
from django.db.models import QuerySet

from app_analytics import constants
from app_analytics.cache import APIUsageCache
from app_analytics.influxdb_wrapper import InfluxDBWrapper, build_filter_string
from app_analytics.models import FeatureEvaluationBucket, Resource
from app_analytics.tasks import track_request
from app_analytics.types import Labels
from environments.models import Environment
from features.models import Feature

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


def get_features_in_use(
    environment: Environment,
    since: datetime | None = None,
) -> QuerySet[Feature] | None:
    """Obtain features found in recent analytics data, i.e. in use"""
    if settings.USE_POSTGRES_FOR_ANALYTICS:
        feature_names = _get_feature_names_in_use_from_analytics_db(environment, since)
    elif settings.INFLUXDB_TOKEN:
        feature_names = _get_feature_names_in_use_from_influxdb(environment, since)
    else:
        return None
    features_in_use: QuerySet[Feature] = Feature.objects.filter(
        name__in=feature_names,
        project__environments=environment,
    )
    return features_in_use


def _get_feature_names_in_use_from_analytics_db(
    environment: Environment,
    since: datetime | None = None,
) -> list[str]:
    # NOTE: Neighbour buckets may bleed depending on `since`
    buckets = FeatureEvaluationBucket.objects.filter(
        environment_id=environment.pk,
        bucket_size=constants.ANALYTICS_READ_BUCKET_SIZE,
        created_at__gte=since,
        total_count__gt=0,
    )
    feature_names = buckets.values_list("feature_name", flat=True).distinct()
    return list(feature_names)


def _get_feature_names_in_use_from_influxdb(
    environment: Environment,
    since: datetime | None = None,
) -> list[str]:
    results = InfluxDBWrapper.influx_query_manager(
        date_start=since,
        filters=build_filter_string(
            [
                'r._measurement == "feature_evaluation"',
                'r["_field"] == "request_count"',
                f'r["environment_id"] == "{environment.pk}"',
            ]
        ),
        extra=(
            '|> keep(columns: ["feature_id"]) '
            '|> distinct(column: "feature_id") '
            '|> yield(name: "distinct")'
        ),
    )
    return [
        feature_name
        for table in results
        for record in table.records
        if (feature_name := record.get_value()) is not None
    ]
