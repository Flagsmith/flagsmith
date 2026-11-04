from datetime import date, datetime

import pytest
from influxdb_client.client.flux_table import FluxRecord, FluxTable

from app_analytics.dataclasses import FeatureEvaluationData, UsageData
from app_analytics.mappers import (
    map_annotated_api_usage_buckets_to_usage_data,
    map_flux_tables_to_feature_evaluation_data,
    map_flux_tables_to_usage_data,
    map_influx_record_values_to_labels,
    map_usage_data_to_daily_totals,
    map_user_agent_to_sdk_language_and_version,
    map_user_agent_to_sdk_user_agent,
)
from app_analytics.models import Resource
from app_analytics.types import AnnotatedAPIUsageBucket


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


def test_map_flux_tables_to_feature_evaluation_data__null_value__returns_zero_count() -> (
    None
):
    # Given
    flux_table = FluxTable()
    flux_table.records.append(
        FluxRecord(
            flux_table,
            values={
                "_time": datetime.fromisoformat("2023-10-01T00:00:00Z"),
                "_value": None,
                "feature_name": "feature_1",
                "client_application_name": "test-app",
            },
        )
    )

    # When
    result = map_flux_tables_to_feature_evaluation_data(flux_tables=[flux_table])

    # Then
    assert result == [
        FeatureEvaluationData(
            day=date(2023, 10, 1),
            count=0,
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
    flux_table.records.append(
        FluxRecord(
            flux_table,
            values={
                "_time": datetime.fromisoformat("2023-10-01T00:00:00Z"),
                "_value": None,
                "resource": "traits",
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


def test_map_flux_tables_to_usage_data__grouped_records__maps_tags_to_ids() -> None:
    # Given
    flux_table = FluxTable()
    flux_table.records.append(
        FluxRecord(
            flux_table,
            values={
                "_time": datetime.fromisoformat("2023-10-01T00:00:00Z"),
                "_value": 3,
                "resource": "flags",
                "project_id": "12",
                "environment_id": "34",
            },
        ),
    )

    # When
    result = map_flux_tables_to_usage_data(flux_tables=[flux_table])

    # Then
    assert result == [
        UsageData(
            day=date(2023, 10, 1),
            flags=3,
            labels={},
            project_id=12,
            environment_id=34,
        )
    ]


def test_map_annotated_api_usage_buckets_to_usage_data__two_environments_same_project__sums_into_one_row() -> (
    None
):
    # Given
    rows = [
        AnnotatedAPIUsageBucket(
            created_at__date=date(2023, 10, 1),
            resource=Resource.FLAGS,
            labels={},
            count=count,
            project_id=1,
        )
        for count in (10, 5)
    ]

    # When
    result = map_annotated_api_usage_buckets_to_usage_data(rows)

    # Then
    assert result == [
        UsageData(day=date(2023, 10, 1), flags=15, labels={}, project_id=1)
    ]


@pytest.mark.parametrize(
    "values, expected",
    [
        ({"user_agent": "50001"}, {"user_agent": "flagsmith-js-sdk/9.3.1"}),
        ({"user_agent": "0"}, {"user_agent": "flagsmith-dotnet-sdk/unknown"}),
        ({"user_agent": "90000"}, {"user_agent": "flagsmith-python-sdk/unknown"}),
        ({"user_agent": "130001"}, {"user_agent": "flagsmith-cli/2.0.0"}),
        ({"user_agent": "140000"}, {"user_agent": "flagsmith-edge-proxy/unknown"}),
        (
            {"user_agent": "150000"},
            {"user_agent": "flagsmith-edge-proxy-python/unknown"},
        ),
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


@pytest.mark.parametrize(
    "user_agent, expected",
    [
        ("flagsmith-python-sdk/6.2.3", ("python", "6.2.3")),
        ("flagsmith-swift-ios-sdk/99.0.0", ("swift-ios", "unknown")),
        ("curl/8.0", ("unknown", "unknown")),
        (None, ("unknown", "unknown")),
        ("flagsmith-cli/2.0.0 (linux/amd64)", ("cli", "2.0.0")),
    ],
    ids=["known-version", "untracked-version", "not-an-sdk", "missing", "cli"],
)
def test_map_user_agent_to_sdk_language_and_version__user_agent__returns_language_and_version(
    user_agent: str | None,
    expected: tuple[str, str],
) -> None:
    # Given / When
    result = map_user_agent_to_sdk_language_and_version(user_agent)

    # Then
    assert result == expected


@pytest.mark.parametrize(
    "user_agent, expected",
    [
        ("flagsmith-python-sdk/6.2.3", "flagsmith-python-sdk/6.2.3"),
        ("flagsmith-python-sdk/99.0.0", "flagsmith-python-sdk/unknown"),
        ("flagsmith-cli/2.0.0 (linux/amd64)", "flagsmith-cli/2.0.0"),
        ("flagsmith-cli/99.0.0 (darwin/arm64)", "flagsmith-cli/unknown"),
        ("flagsmith-edge-proxy/99.0.0", "flagsmith-edge-proxy/unknown"),
        (
            "flagsmith-edge-proxy-python/99.0.0",
            "flagsmith-edge-proxy-python/unknown",
        ),
        ("python-httpx/0.28.1", None),
        ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)", None),
        ("", None),
    ],
    ids=[
        "known-sdk-version",
        "untracked-sdk-version",
        "known-version-with-comment",
        "untracked-version-with-comment",
        "edge-proxy",
        "edge-proxy-python",
        "unknown-client",
        "browser",
        "empty",
    ],
)
def test_map_user_agent_to_sdk_user_agent__user_agent__returns_expected(
    user_agent: str,
    expected: str | None,
) -> None:
    # Given / When
    result = map_user_agent_to_sdk_user_agent(user_agent)

    # Then
    assert result == expected


def test_map_usage_data_to_daily_totals__multiple_labels_per_day__sums_across_labels() -> (
    None
):
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
