from datetime import date, datetime

import pytest
from influxdb_client.client.flux_table import FluxRecord, FluxTable

from app_analytics.dataclasses import FeatureEvaluationData, UsageData
from app_analytics.mappers import (
    map_flux_tables_to_feature_evaluation_data,
    map_flux_tables_to_usage_data,
    map_influx_record_values_to_labels,
)


def test_map_flux_tables_to_feature_evaluation_data__returns_expected() -> None:
    # Given
    flux_table = FluxTable()
    flux_table.records.append(
        FluxRecord(
            flux_table,
            values={
                "_time": datetime.fromisoformat("2023-10-01T00:00:00Z"),
                "_value": 5,
                "feature_name": "feature_1",
                "client_application_name": "test-app",
                "unrelated": "value",
            },
        )
    )

    # When
    result = map_flux_tables_to_feature_evaluation_data(flux_tables=[flux_table])

    # Then
    assert result == [
        FeatureEvaluationData(
            day=date(2023, 10, 1),
            count=5,
            labels={"client_application_name": "test-app"},
        )
    ]


def test_map_flux_tables_to_usage_data__returns_expected() -> None:
    # Given
    flux_table = FluxTable()
    flux_table.records.append(
        FluxRecord(
            flux_table,
            values={
                "_time": datetime.fromisoformat("2023-10-01T00:00:00Z"),
                "_value": 10,
                "resource": "flags",
                "client_application_name": "test-app",
                "unrelated": "value",
            },
        ),
    )
    flux_table.records.append(
        FluxRecord(
            flux_table,
            values={
                "_time": datetime.fromisoformat("2023-10-01T00:00:00Z"),
                "_value": 10,
                "resource": "identities",
                "client_application_name": "test-app",
                "unrelated": "value",
            },
        ),
    )

    # When
    result = map_flux_tables_to_usage_data(flux_tables=[flux_table])

    # Then
    assert result == [
        UsageData(
            day=date(2023, 10, 1),
            flags=10,
            traits=0,
            identities=10,
            labels={"client_application_name": "test-app"},
        )
    ]


@pytest.mark.parametrize(
    "values, expected",
    [
        ({"user_agent": "50001"}, {"user_agent": "flagsmith-js-sdk/9.3.1"}),
        ({"user_agent": "0"}, {"user_agent": "flagsmith-dotnet-sdk/unknown"}),
        ({"user_agent": "90000"}, {"user_agent": "flagsmith-python-sdk/unknown"}),
        ({}, {}),
        ({"user_agent": "99999"}, {}),
        ({"user_agent": "not-a-number"}, {}),
    ],
)
def test_map_influx_record_values_to_labels(
    values: dict[str, str],
    expected: dict[str, str],
) -> None:
    # Given / When
    result = map_influx_record_values_to_labels(values)

    # Then
    assert result == expected
