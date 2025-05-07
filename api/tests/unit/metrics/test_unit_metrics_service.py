from typing import Callable

import pytest

from metrics.metrics_service import build_metrics
from metrics.types import EnvMetricsEntities, EnvMetricsName, MetricDefinition


@pytest.fixture
def metrics_querysets() -> dict[EnvMetricsName, Callable[[], int]]:
    return {
        EnvMetricsName.TOTAL_FEATURES: lambda: 10,
        EnvMetricsName.ENABLED_FEATURES: lambda: 5,
        EnvMetricsName.SEGMENT_OVERRIDES: lambda: 15,
    }


@pytest.fixture
def metrics_definitions() -> list[MetricDefinition]:
    return [
        {
            "name": EnvMetricsName.ENABLED_FEATURES,
            "description": "Enabled feature count",
            "entity": EnvMetricsEntities.FEATURES,
            "rank": 2,
        },
        {
            "name": EnvMetricsName.SEGMENT_OVERRIDES,
            "description": "Segment overrides count",
            "entity": EnvMetricsEntities.SEGMENTS,
            "disabled": True,
            "rank": 3,
        },
        {
            "name": EnvMetricsName.TOTAL_FEATURES,
            "description": "Total feature count",
            "entity": EnvMetricsEntities.FEATURES,
            "rank": 1,
        },
    ]


def test_build_metrics_filters_and_formats(
    metrics_querysets: dict[EnvMetricsName, Callable[[], int]],
    metrics_definitions: list[MetricDefinition],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "metrics.metrics_service.ALL_METRIC_DEFINITIONS", metrics_definitions
    )

    result = build_metrics(metrics_querysets)

    assert len(result) == 2

    assert result[0] == {
        "name": EnvMetricsName.TOTAL_FEATURES.value,
        "description": "Total feature count",
        "entity": EnvMetricsEntities.FEATURES.value,
        "rank": 1,
        "value": 10,
    }

    assert result[1] == {
        "name": EnvMetricsName.ENABLED_FEATURES.value,
        "description": "Enabled feature count",
        "entity": EnvMetricsEntities.FEATURES.value,
        "rank": 2,
        "value": 5,
    }
