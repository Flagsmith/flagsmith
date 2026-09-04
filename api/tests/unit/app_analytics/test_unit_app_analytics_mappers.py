from datetime import date, datetime

import pytest
from influxdb_client.client.flux_table import FluxRecord, FluxTable

from app_analytics.dataclasses import FeatureEvaluationData, UsageData
from app_analytics.mappers import (
    map_flux_tables_to_feature_evaluation_data,
    map_flux_tables_to_usage_data,
    map_influx_record_values_to_labels,
    map_usage_data_to_daily_totals,
)


def test_map_flux_tables_to_feature_evaluation_data__single_record__returns_expected_data() -> (
    None
):
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


def test_map_flux_tables_to_usage_data__multiple_resources__returns_aggregated_data() -> (
    None
):
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
def test_map_influx_record_values_to_labels__various_user_agents__returns_expected_labels(
    values: dict[str, str],
    expected: dict[str, str],
) -> None:
    # Given / When
    result = map_influx_record_values_to_labels(values)

    # Then
    assert result == expected


def test_map_usage_data_to_daily_totals__multiple_labels_per_day__sums_across_labels() -> (
    None
):
    """
    Usage data holds a row per day and labels combination, so a day with
    traffic from several client applications arrives as several rows. Totals
    must sum across them, or a single client is reported as the whole
    organisation's usage.
    """
    # Given
    usage_data = [
        UsageData(
            day=date(2026, 6, 27),
            flags=3_158,
            labels={"client_application_name": "small-app"},
        ),
        UsageData(
            day=date(2026, 6, 27),
            flags=238_574,
            identities=10,
            labels={"client_application_name": "busy-app"},
        ),
        UsageData(
            day=date(2026, 6, 28),
            flags=240_000,
            traits=5,
            environment_document=1,
            labels={"client_application_name": "busy-app"},
        ),
    ]

    # When
    labels, totals = map_usage_data_to_daily_totals(usage_data)

    # Then
    assert labels == ["2026-06-27", "2026-06-28"]
    assert totals == {
        "flags": [241_732, 240_000],
        "identities": [10, 0],
        "traits": [0, 5],
        "environment_document": [0, 1],
    }


def test_map_usage_data_to_daily_totals__unordered_days__returns_days_in_order() -> (
    None
):
    # Given
    usage_data = [
        UsageData(day=date(2026, 6, 28), flags=2),
        UsageData(day=date(2026, 6, 26), flags=1),
        UsageData(day=date(2026, 6, 27), flags=3),
    ]

    # When
    labels, totals = map_usage_data_to_daily_totals(usage_data)

    # Then
    assert labels == ["2026-06-26", "2026-06-27", "2026-06-28"]
    assert totals["flags"] == [1, 3, 2]


def test_map_usage_data_to_daily_totals__no_usage_data__returns_empty_series() -> None:
    # Given / When
    labels, totals = map_usage_data_to_daily_totals([])

    # Then
    assert labels == []
    assert totals == {
        "flags": [],
        "identities": [],
        "traits": [],
        "environment_document": [],
    }
