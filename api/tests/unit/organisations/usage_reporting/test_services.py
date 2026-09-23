import json
from datetime import datetime, timezone

import pytest
from django.conf import settings as django_settings
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from organisations.models import Organisation
from organisations.usage_reporting.dataclasses import (
    ApiCallBreakdown,
    ProjectUsage,
    UsageSnapshot,
)
from organisations.usage_reporting.services import (
    get_licensed_organisations,
    push_snapshot,
    push_usage_snapshots,
)


@pytest.fixture
def snapshot() -> UsageSnapshot:
    return UsageSnapshot(
        timestamp=datetime(2026, 6, 18, 8, 0, 0, tzinfo=timezone.utc),
        seat_count=3,
        api_call_total=10,
        api_call_breakdown=ApiCallBreakdown(
            flags=1, identities=2, traits=3, environment_documents=4
        ),
        project_count=1,
        instance_version="2.142.3",
        project_usage=[ProjectUsage(project_id=1, api_call_count=10)],
    )


def test_get_licensed_organisations__licensing_not_installed__returns_empty(
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.LICENSING_INSTALLED = False

    # When / Then
    assert get_licensed_organisations() == []


@pytest.mark.skipif(
    not django_settings.LICENSING_INSTALLED,
    reason="the licence relation requires the optional licensing package",
)
def test_get_licensed_organisations__organisation_without_licence__excluded(
    settings: SettingsWrapper,
    organisation: Organisation,
) -> None:
    # Given
    settings.LICENSING_INSTALLED = True

    # When / Then - the unlicensed organisation is filtered out
    assert get_licensed_organisations() == []


@pytest.mark.parametrize(
    "status_code, event, level",
    [
        (201, "snapshot.pushed", "info"),
        (200, "snapshot.pushed", "info"),
        (400, "snapshot.push_failed", "warning"),
        (401, "snapshot.push_failed", "warning"),
        (403, "snapshot.push_failed", "warning"),
        (429, "snapshot.push_failed", "warning"),
        (500, "snapshot.push_failed", "warning"),
        (503, "snapshot.push_failed", "warning"),
        (418, "snapshot.push_failed", "warning"),
    ],
)
def test_push_snapshot__status_code__logs_expected_event(
    mocker: MockerFixture,
    log: StructuredLogCapture,
    snapshot: UsageSnapshot,
    status_code: int,
    event: str,
    level: str,
) -> None:
    # Given
    mocked_post = mocker.patch("organisations.usage_reporting.services.requests.post")
    mocked_post.return_value.status_code = status_code
    mocked_post.return_value.ok = status_code < 400

    # When
    push_snapshot(
        base_url="https://cp.example.com/",
        snapshot=snapshot,
        signature_b64="c2ln",
    )

    # Then
    assert log.has(event, level=level, status_code=status_code)


def test_push_snapshot__valid_snapshot__sends_bearer_authed_post(
    mocker: MockerFixture,
    snapshot: UsageSnapshot,
) -> None:
    # Given
    mocked_post = mocker.patch("organisations.usage_reporting.services.requests.post")
    mocked_post.return_value.status_code = 201
    signature_b64 = "++++ABE="

    # When
    push_snapshot(
        base_url="https://cp.example.com/",
        snapshot=snapshot,
        signature_b64=signature_b64,
    )

    # Then
    mocked_post.assert_called_once()
    (url,), kwargs = mocked_post.call_args
    assert url == "https://cp.example.com/v1/public/usage"
    # The signature's raw bytes, unpadded base64url-encoded for the wire.
    assert kwargs["headers"]["Authorization"] == "Bearer ----ABE"
    assert kwargs["headers"]["Content-Type"] == "application/json"
    assert json.loads(kwargs["data"]) == {
        "timestamp": "2026-06-18T08:00:00Z",
        "seat_count": 3,
        "api_call_total": 10,
        "api_call_breakdown": {
            "flags": 1,
            "identities": 2,
            "traits": 3,
            "environment_documents": 4,
        },
        "project_count": 1,
        "instance_version": "2.142.3",
        "project_usage": [{"project_id": 1, "api_call_count": 10}],
    }


def test_push_usage_snapshots__control_plane_url_unset__no_op(
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.CONTROL_PLANE_URL = None
    mocked_get_orgs = mocker.patch(
        "organisations.usage_reporting.services.get_licensed_organisations"
    )
    mocked_push = mocker.patch("organisations.usage_reporting.services.push_snapshot")

    # When
    push_usage_snapshots()

    # Then
    mocked_get_orgs.assert_not_called()
    mocked_push.assert_not_called()


def test_push_usage_snapshots__no_licensed_organisations__no_op(
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.CONTROL_PLANE_URL = "https://cp.example.com"
    mocker.patch(
        "organisations.usage_reporting.services.get_licensed_organisations",
        return_value=[],
    )
    mocked_push = mocker.patch("organisations.usage_reporting.services.push_snapshot")

    # When
    push_usage_snapshots()

    # Then
    mocked_push.assert_not_called()


def test_push_usage_snapshots__licensed_organisations__pushes_each(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    snapshot: UsageSnapshot,
) -> None:
    # Given
    settings.CONTROL_PLANE_URL = "https://cp.example.com"
    org_one = mocker.Mock(id=1, licence=mocker.Mock(signature="sig-1"))
    org_two = mocker.Mock(id=2, licence=mocker.Mock(signature="sig-2"))
    mocker.patch(
        "organisations.usage_reporting.services.get_licensed_organisations",
        return_value=[org_one, org_two],
    )
    mocker.patch(
        "organisations.usage_reporting.services.map_organisation_to_usage_snapshot",
        return_value=snapshot,
    )
    mocked_push = mocker.patch("organisations.usage_reporting.services.push_snapshot")

    # When
    push_usage_snapshots()

    # Then
    assert mocked_push.call_count == 2
    mocked_push.assert_any_call(
        base_url="https://cp.example.com", snapshot=snapshot, signature_b64="sig-1"
    )
    mocked_push.assert_any_call(
        base_url="https://cp.example.com", snapshot=snapshot, signature_b64="sig-2"
    )


def test_push_usage_snapshots__one_organisation_raises__continues(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    log: StructuredLogCapture,
    snapshot: UsageSnapshot,
) -> None:
    # Given
    settings.CONTROL_PLANE_URL = "https://cp.example.com"
    org_one = mocker.Mock(id=1, licence=mocker.Mock(signature="sig-1"))
    org_two = mocker.Mock(id=2, licence=mocker.Mock(signature="sig-2"))
    mocker.patch(
        "organisations.usage_reporting.services.get_licensed_organisations",
        return_value=[org_one, org_two],
    )
    mocker.patch(
        "organisations.usage_reporting.services.map_organisation_to_usage_snapshot",
        side_effect=[ValueError("boom"), snapshot],
    )
    mocked_push = mocker.patch("organisations.usage_reporting.services.push_snapshot")

    # When
    push_usage_snapshots()

    # Then - first organisation failed (logged) but second still pushed
    assert log.has("snapshot.errored", level="error")
    mocked_push.assert_called_once_with(
        base_url="https://cp.example.com", snapshot=snapshot, signature_b64="sig-2"
    )
