from unittest.mock import MagicMock

import pytest

from environments.models import Environment
from features.models import Feature
from metrics.metrics_service import EnvironmentMetricsService
from metrics.types import EnvMetricsName


@pytest.mark.parametrize("with_workflows", [True, False])
@pytest.mark.django_db
def test_environment_metrics_service_builds_expected_metrics(
    monkeypatch: pytest.MonkeyPatch,
    environment: Environment,
    with_workflows: bool,
) -> None:
    # Given
    mock_agg = {"total": 10, "enabled": 5}
    mock_features_qs = MagicMock()
    mock_features_qs.aggregate.return_value = mock_agg

    monkeypatch.setattr(
        environment, "get_features_metrics_queryset", lambda: mock_features_qs
    )
    monkeypatch.setattr(
        environment, "get_segment_metrics_queryset", lambda: MagicMock(count=lambda: 3)
    )
    monkeypatch.setattr(
        environment,
        "get_identity_overrides_queryset",
        lambda: MagicMock(count=lambda: 7),
    )
    monkeypatch.setattr(
        environment,
        "get_change_requests_metrics_queryset",
        lambda: MagicMock(count=lambda: 2),
    )
    monkeypatch.setattr(
        environment,
        "get_scheduled_metrics_queryset",
        lambda: MagicMock(count=lambda: 1),
    )

    environment.project.enable_dynamo_db = False
    environment.minimum_change_request_approvals = 1 if with_workflows else None

    # When
    service = EnvironmentMetricsService(environment)
    metrics = service.get_metrics_payload()
    expected_count_metrics = 6 if with_workflows else 4
    # Then
    assert len(metrics) == expected_count_metrics

    assert metrics[0]["name"] == EnvMetricsName.TOTAL_FEATURES.value
    assert metrics[0]["value"] == 10

    assert metrics[1]["name"] == EnvMetricsName.ENABLED_FEATURES.value
    assert metrics[1]["value"] == 5

    assert metrics[2]["name"] == EnvMetricsName.SEGMENT_OVERRIDES.value
    assert metrics[2]["value"] == 3

    assert metrics[3]["name"] == EnvMetricsName.IDENTITY_OVERRIDES.value
    assert metrics[3]["value"] == 7

    if with_workflows:
        assert metrics[4]["name"] == EnvMetricsName.OPEN_CHANGE_REQUESTS.value
        assert metrics[4]["value"] == 2
        assert metrics[5]["name"] == EnvMetricsName.TOTAL_SCHEDULED_CHANGES.value
        assert metrics[5]["value"] == 1


@pytest.mark.parametrize("uses_dynamo, expected_value", [(True, 99), (False, 1)])
def test_dynamo_identity_metric_used(
    monkeypatch: pytest.MonkeyPatch,
    environment: Environment,
    uses_dynamo: bool,
    expected_value: int,
) -> None:
    # Given
    environment.project.enable_dynamo_db = uses_dynamo
    monkeypatch.setattr(
        environment, "get_segment_metrics_queryset", lambda: MagicMock(count=lambda: 1)
    )
    Feature.objects.create(
        id=10,
        project=environment.project,
        name="feature-10",
        is_archived=False,
        deleted_at=None,
    )
    identity_count_mock = MagicMock(return_value=1)
    monkeypatch.setattr(
        environment,
        "get_identity_overrides_queryset",
        lambda: MagicMock(count=identity_count_mock),
    )

    dynamo_mock = MagicMock(return_value={10: 99})
    monkeypatch.setattr(
        "edge_api.identities.models.EdgeIdentity.dynamo_wrapper.get_identity_override_feature_counts",
        dynamo_mock,
    )
    # When
    metrics_service = EnvironmentMetricsService(environment)
    metrics = metrics_service.get_metrics_payload()
    # Then
    assert metrics_service.uses_dynamo == uses_dynamo
    assert any(
        m["name"] == EnvMetricsName.IDENTITY_OVERRIDES.value
        and m["value"] == expected_value
        for m in metrics
    )

    if uses_dynamo:
        dynamo_mock.assert_called_once()
        identity_count_mock.assert_not_called()
    else:
        identity_count_mock.assert_called_once()
        dynamo_mock.assert_not_called()
