from typing import Any, Iterable

from django.http import HttpRequest
from influxdb_client.client.flux_table import FluxTable
from pydantic import Field, create_model
from pydantic.type_adapter import TypeAdapter

from app_analytics.constants import TRACK_HEADERS
from app_analytics.dataclasses import FeatureEvaluationData, UsageData
from app_analytics.models import Resource
from app_analytics.types import (
    AnnotatedAPIUsageBucket,
    AnnotatedAPIUsageKey,
    Labels,
)

_request_header_labels_model_fields: dict[str, Any] = {
    str(label): (str | None, Field(default=None, alias=header))
    for header, label in TRACK_HEADERS.items()
}
_RequestHeaderLabelsModel = create_model(
    "_RequestHeaderLabelsModel",
    **_request_header_labels_model_fields,
)
_labels_type_adapter: TypeAdapter[Labels] = TypeAdapter(Labels)


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
    return [
        UsageData(
            day=(values := record.values)["_time"].strftime("%Y-%m-%d"),
            labels=_labels_type_adapter.validate_python(values),
            **{values["resource"]: values["_value"]},
        )
        for flux_table in flux_tables
        for record in flux_table.records
    ]


def map_flux_tables_to_feature_evaluation_data(
    flux_tables: list[FluxTable],
) -> list[FeatureEvaluationData]:
    return [
        FeatureEvaluationData(
            day=(values := record.values)["_time"].strftime("%Y-%m-%d"),
            count=values["_value"],
            labels=_labels_type_adapter.validate_python(values),
        )
        for flux_table in flux_tables
        for record in flux_table.records
    ]


def map_request_to_labels(request: HttpRequest) -> Labels:
    result: Labels = _RequestHeaderLabelsModel.model_validate(
        request.headers,
    ).model_dump(
        exclude_unset=True,
    )
    return result
