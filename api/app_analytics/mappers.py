from collections import defaultdict
from typing import Annotated, Any, Iterable, cast

from django.http import HttpRequest
from influxdb_client.client.flux_table import FluxTable
from pydantic import BeforeValidator, Field, create_model

from app_analytics.constants import (
    LABELS,
    SDK_INFLUX_IDS_BY_USER_AGENT,
    SDK_USER_AGENT_KNOWN_VERSIONS,
    SDK_USER_AGENTS_BY_INFLUX_ID,
    TRACK_HEADERS,
)
from app_analytics.dataclasses import FeatureEvaluationData, UsageData
from app_analytics.models import FeatureEvaluationRaw, Resource
from app_analytics.types import (
    AnnotatedAPIUsageBucket,
    AnnotatedAPIUsageKey,
    FeatureEvaluationCacheKey,
    InputLabels,
    KnownSDK,
    Labels,
    TrackFeatureEvaluationsByEnvironmentData,
    TrackFeatureEvaluationsByEnvironmentKwargs,
)
from integrations.flagsmith.client import get_client


def map_user_agent_to_sdk_user_agent(value: str) -> str | None:
    sdk_name, _, sdk_version = value.partition("/")
    if sdk_name in SDK_USER_AGENT_KNOWN_VERSIONS:
        if sdk_version in SDK_USER_AGENT_KNOWN_VERSIONS[cast(KnownSDK, sdk_name)]:
            return value
        return f"{sdk_name}/unknown"
    return None


_request_header_labels_model_fields: dict[str, Any] = {
    str(label): (
        Annotated[str | None, BeforeValidator(map_user_agent_to_sdk_user_agent)]
        if label in ("user_agent", "sdk_user_agent")
        else str | None,
        Field(default=None, alias=header),
    )
    for header, label in TRACK_HEADERS.items()
}
_RequestHeaderLabelsModel = create_model(
    "_RequestHeaderLabelsModel",
    **_request_header_labels_model_fields,
)


def map_labels_to_influx_record_values(labels: Labels) -> dict[str, Any]:
    influx_record_values: dict[str, Any] = {}
    for label, value in labels.items():
        if label == "user_agent":
            if (influx_id := SDK_INFLUX_IDS_BY_USER_AGENT.get(value)) is not None:
                influx_record_values["user_agent"] = influx_id
            continue
        influx_record_values[label] = value
    return influx_record_values


def map_influx_record_values_to_labels(values: dict[str, Any]) -> Labels:
    labels: Labels = {}
    for label in LABELS:
        if label == "user_agent":
            user_agent_influx_id: int | None = values.get("user_agent")
            if user_agent_influx_id and (
                user_agent := SDK_USER_AGENTS_BY_INFLUX_ID.get(user_agent_influx_id)
            ):
                labels["user_agent"] = user_agent
            continue
        if value := values.get(label):
            labels[label] = value
    return labels


def map_annotated_api_usage_buckets_to_usage_data(
    api_usage_buckets: Iterable[AnnotatedAPIUsageBucket],
) -> list[UsageData]:
    """
    Aggregates API usage data buckets by date and labels.
    Each resulting `UsageData` object contains the total count for each resource
    for that date and labels combination.
    """
    data_by_key: dict[AnnotatedAPIUsageKey, UsageData] = {}
    for row in api_usage_buckets:
        date = row["created_at__date"]
        labels = row["labels"]
        key = AnnotatedAPIUsageKey(
            date=date,
            labels=tuple(labels.items()),
        )
        if key not in data_by_key:
            data_by_key[key] = UsageData(
                day=date,
                labels=labels,
            )
        if column_name := Resource(row["resource"]).column_name:
            setattr(
                data_by_key[key],
                column_name,
                row["count"],
            )
    return list(data_by_key.values())


def map_flux_tables_to_usage_data(
    flux_tables: list[FluxTable],
) -> list[UsageData]:
    """
    Aggregates API usage data buckets by date and labels.
    Each resulting `UsageData` object contains the total count for each resource
    for that date and labels combination.
    """
    data_by_key: dict[AnnotatedAPIUsageKey, UsageData] = {}
    for flux_table in flux_tables:
        for record in flux_table.records:
            values = record.values
            date = values["_time"].date()
            labels: Labels = map_influx_record_values_to_labels(values)
            key = AnnotatedAPIUsageKey(
                date=date,
                labels=tuple(labels.items()),
            )
            if key not in data_by_key:
                data_by_key[key] = UsageData(
                    day=date,
                    labels=labels,
                )
            if (resource := Resource.get_from_name(values["resource"])) and (
                resource_attr := resource.column_name
            ):
                setattr(
                    data_by_key[key],
                    resource_attr,
                    values["_value"],
                )
    return list(data_by_key.values())


def map_flux_tables_to_feature_evaluation_data(
    flux_tables: list[FluxTable],
) -> list[FeatureEvaluationData]:
    return [
        FeatureEvaluationData(
            day=(values := record.values)["_time"].date(),
            count=values["_value"],
            labels=map_influx_record_values_to_labels(values),
        )
        for flux_table in flux_tables
        for record in flux_table.records
    ]


def map_input_labels_to_labels(input_labels: InputLabels) -> Labels:
    labels: Labels = {}
    for label, value in input_labels.items():
        if label == "sdk_user_agent" or label == "user_agent":
            labels["user_agent"] = value
            continue
        labels[label] = value
    return labels


def map_request_to_labels(request: HttpRequest) -> Labels:
    if not (
        get_client("local", local_eval=True)
        .get_environment_flags()
        .is_feature_enabled("sdk_metrics_labels")
    ):
        return {}
    input_labels: InputLabels = _RequestHeaderLabelsModel.model_validate(
        request.headers,
    ).model_dump(
        exclude_unset=True,
        exclude_none=True,
    )
    return map_input_labels_to_labels(input_labels)


def map_feature_evaluation_cache_to_track_feature_evaluations_by_environment_kwargs(
    cache: dict[FeatureEvaluationCacheKey, int],
) -> list[TrackFeatureEvaluationsByEnvironmentKwargs]:
    feature_evaluations_by_environment: dict[
        int, list[TrackFeatureEvaluationsByEnvironmentData]
    ] = defaultdict(list)

    for cache_key, evaluation_count in cache.items():
        environment_id = cache_key.environment_id
        feature_evaluations_by_environment[environment_id].append(
            {
                "feature_name": cache_key.feature_name,
                "labels": dict(cache_key.labels),
                "evaluation_count": evaluation_count,
            }
        )

    return [
        {
            "environment_id": environment_id,
            "feature_evaluations": feature_evaluations,
        }
        for environment_id, feature_evaluations in feature_evaluations_by_environment.items()
    ]


def map_feature_evaluation_data_to_feature_evaluation_raw(
    environment_id: int,
    feature_evaluations: list[TrackFeatureEvaluationsByEnvironmentData],
) -> list[FeatureEvaluationRaw]:
    return [
        FeatureEvaluationRaw(
            environment_id=environment_id,
            feature_name=feature_evaluation["feature_name"],
            evaluation_count=feature_evaluation["evaluation_count"],
            labels=feature_evaluation["labels"],
        )
        for feature_evaluation in feature_evaluations
    ]
