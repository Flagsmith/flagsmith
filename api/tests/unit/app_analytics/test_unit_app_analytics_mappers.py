from datetime import date, datetime

from influxdb_client.client.flux_table import FluxRecord, FluxTable

from app_analytics.dataclasses import FeatureEvaluationData, UsageData
from app_analytics.mappers import (
    map_flux_tables_to_feature_evaluation_data,
    map_flux_tables_to_usage_data,
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
