from collections import defaultdict
from functools import partial
from typing import Any, Iterable

from django.http import HttpRequest
from fastuaparser import parse_ua  # type: ignore[import-untyped]
from influxdb_client.client.flux_table import FluxTable
from pydantic import Field, create_model
from pydantic.type_adapter import TypeAdapter

from app_analytics.constants import LABELS, TRACK_HEADERS
from app_analytics.dataclasses import FeatureEvaluationData, UsageData
from app_analytics.models import FeatureEvaluationRaw, Resource
from app_analytics.types import (
    AnnotatedAPIUsageBucket,
    AnnotatedAPIUsageKey,
    FeatureEvaluationCacheKey,
    InputLabels,
    Labels,
    TrackFeatureEvaluationsByEnvironmentData,
    TrackFeatureEvaluationsByEnvironmentKwargs,
)
from integrations.flagsmith.client import get_client

_request_header_labels_model_fields: dict[str, Any] = {
    str(label): (str | None, Field(default=None, alias=header))
    for header, label in TRACK_HEADERS.items()
}
_RequestHeaderLabelsModel = create_model(
    "_RequestHeaderLabelsModel",
    **_request_header_labels_model_fields,
)
_labels_type_adapter: TypeAdapter[Labels] = TypeAdapter(Labels)

map_influx_record_values_to_labels = partial(
    _labels_type_adapter.dump_python,
    include=set(LABELS),
)


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
            if resource := values.get("resource"):
                setattr(
                    data_by_key[key],
                    resource,
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
        if label == "sdk_user_agent":
            labels["user_agent"] = value
            continue
        elif label == "user_agent":
            # fastuaparser classifies unrecognized UAs as "Other" — assume these to
            # represent server-side SDKs.
            parsed_ua_string: str = parse_ua(value)
            is_server_side_sdk = parsed_ua_string.startswith("Other - ")

            # Skip browser SDKs that don't send the special header
            if not is_server_side_sdk:
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
    labels: InputLabels = _RequestHeaderLabelsModel.model_validate(
        request.headers,
    ).model_dump(
        exclude_unset=True,
    )
    return map_input_labels_to_labels(labels)


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
