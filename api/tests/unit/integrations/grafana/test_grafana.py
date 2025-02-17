import json

import pytest
import responses
from pytest_mock import MockerFixture

from audit.models import AuditLog
from integrations.grafana.grafana import GrafanaWrapper


@pytest.mark.parametrize("base_url", ["test.com", "test.com/"])
def test_grafana_wrapper__base_url__expected_url(base_url: str) -> None:
    # When
    wrapper = GrafanaWrapper(base_url=base_url, api_key="any")

    # Then
    assert wrapper.url == "test.com/api/annotations"


@responses.activate()
def test_grafana_wrapper__track_event__expected_api_call() -> None:
    # Given
    wrapper = GrafanaWrapper(base_url="https://test.com", api_key="any")
    event = {"sample": "event"}

    responses.add(url="https://test.com/api/annotations", method="POST", status=200)

    # When
    wrapper._track_event(event)

    # Then
    assert len(responses.calls) == 1
    assert responses.calls[0].request.headers["Authorization"] == "Bearer any"  # type: ignore[union-attr]
    assert responses.calls[0].request.headers["Content-Type"] == "application/json"  # type: ignore[union-attr]
    assert json.loads(responses.calls[0].request.body) == event  # type: ignore[union-attr]


def test_grafana_wrapper__generate_event_data__return_expected(
    mocker: MockerFixture,
) -> None:
    # Given
    map_audit_log_record_to_grafana_annotation_mock = mocker.patch(
        "integrations.grafana.grafana.map_audit_log_record_to_grafana_annotation",
        autospec=True,
    )
    audit_log_record_mock = mocker.MagicMock(spec=AuditLog)

    # When
    event_data = GrafanaWrapper.generate_event_data(audit_log_record_mock)

    # Then
    map_audit_log_record_to_grafana_annotation_mock.assert_called_once_with(
        audit_log_record_mock
    )
    assert event_data == map_audit_log_record_to_grafana_annotation_mock.return_value
