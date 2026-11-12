import json
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
import requests
from django.conf import settings as django_settings
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from organisations.models import Organisation, UsageReportingState
from organisations.usage_reporting.dataclasses import (
    ApiCallBreakdown,
    ProjectUsage,
    UsageSnapshot,
)
from organisations.usage_reporting.services import (
    RETRY_POLICY,
    get_licensed_organisations,
    push_snapshot,
    push_usage_snapshots,
)

REPORTED_LONG_AGO = datetime(2000, 1, 1, tzinfo=timezone.utc)


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


@pytest.fixture
def mocked_post(mocker: MockerFixture) -> MagicMock:
    mocked_session = mocker.patch(
        "organisations.usage_reporting.services.requests.Session"
    )
    post: MagicMock = mocked_session.return_value.__enter__.return_value.post
    return post


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


def build_response(status_code: int) -> requests.Response:
    response = requests.Response()
    response.status_code = status_code
    return response


@pytest.mark.parametrize("status_code", [200, 201])
def test_push_snapshot__success_status_code__logs_pushed(
    mocked_post: MagicMock,
    log: StructuredLogCapture,
    snapshot: UsageSnapshot,
    status_code: int,
) -> None:
    # Given
    mocked_post.return_value = build_response(status_code)

    # When
    push_snapshot(
        base_url="https://cp.example.com/",
        snapshot=snapshot,
        signature_b64="c2ln",
    )

    # Then
    assert log.has("snapshot.pushed", level="info", status_code=status_code)


@pytest.mark.parametrize("status_code", [400, 401, 403, 418, 429, 500, 503])
def test_push_snapshot__error_status_code__raises_http_error(
    mocked_post: MagicMock,
    log: StructuredLogCapture,
    snapshot: UsageSnapshot,
    status_code: int,
) -> None:
    # Given
    mocked_post.return_value = build_response(status_code)

    # When
    with pytest.raises(requests.HTTPError) as exc_info:
        push_snapshot(
            base_url="https://cp.example.com/",
            snapshot=snapshot,
            signature_b64="c2ln",
        )

    # Then
    assert exc_info.value.response.status_code == status_code
    assert not log.has("snapshot.pushed")


def test_push_snapshot__valid_snapshot__mounts_retry_policy(
    mocker: MockerFixture,
    snapshot: UsageSnapshot,
) -> None:
    # Given
    mocked_session = mocker.patch(
        "organisations.usage_reporting.services.requests.Session"
    )
    session = mocked_session.return_value.__enter__.return_value
    session.post.return_value.ok = True

    # When
    push_snapshot(
        base_url="https://cp.example.com/",
        snapshot=snapshot,
        signature_b64="c2ln",
    )

    # Then
    session.mount.assert_called_once()
    prefix, adapter = session.mount.call_args.args
    assert prefix == "https://"
    assert adapter.max_retries is RETRY_POLICY


def test_push_snapshot__valid_snapshot__sends_bearer_authed_post(
    mocked_post: MagicMock,
    snapshot: UsageSnapshot,
) -> None:
    # Given
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
    kwargs = mocked_post.call_args.kwargs
    assert kwargs["url"] == "https://cp.example.com/v1/public/usage"
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
    org_one = mocker.Mock(
        id=1,
        licence=mocker.Mock(signature="sig-1"),
        usage_reporting_state=mocker.Mock(reported_until=REPORTED_LONG_AGO),
    )
    org_two = mocker.Mock(
        id=2,
        licence=mocker.Mock(signature="sig-2"),
        usage_reporting_state=mocker.Mock(reported_until=REPORTED_LONG_AGO),
    )
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


@pytest.fixture
def mocked_map_for_licensed_organisation(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    organisation: Organisation,
    snapshot: UsageSnapshot,
) -> MagicMock:
    settings.CONTROL_PLANE_URL = "https://cp.example.com"
    mocker.patch(
        "organisations.usage_reporting.services.get_licensed_organisations",
        return_value=[organisation],
    )
    # The licence relation only exists with the optional licensing package.
    mocker.patch.object(
        Organisation, "licence", create=True, new=mocker.Mock(signature="sig-1")
    )
    mocker.patch("organisations.usage_reporting.services.push_snapshot")
    mocked_map: MagicMock = mocker.patch(
        "organisations.usage_reporting.services.map_organisation_to_usage_snapshot",
        return_value=snapshot,
    )
    return mocked_map


@pytest.mark.freeze_time("2026-06-18T09:30:00+00:00")
def test_push_usage_snapshots__never_reported__maps_previous_24_hours(
    organisation: Organisation,
    mocked_map_for_licensed_organisation: MagicMock,
) -> None:
    # Given - no UsageReportingState for the organisation

    # When
    push_usage_snapshots()

    # Then - the window ends at the start of the current hour
    mocked_map_for_licensed_organisation.assert_called_once_with(
        organisation=organisation,
        window_start=datetime(2026, 6, 17, 9, 0, 0, tzinfo=timezone.utc),
        window_end=datetime(2026, 6, 18, 9, 0, 0, tzinfo=timezone.utc),
    )


@pytest.mark.freeze_time("2026-06-18T09:30:00+00:00")
def test_push_usage_snapshots__previously_reported__maps_from_reported_until(
    organisation: Organisation,
    mocked_map_for_licensed_organisation: MagicMock,
) -> None:
    # Given - the last successful push ended three days ago
    reported_until = datetime(2026, 6, 15, 9, 0, 0, tzinfo=timezone.utc)
    UsageReportingState.objects.create(
        organisation=organisation, reported_until=reported_until
    )

    # When
    push_usage_snapshots()

    # Then - the unreported period is included in the window
    mocked_map_for_licensed_organisation.assert_called_once_with(
        organisation=organisation,
        window_start=reported_until,
        window_end=datetime(2026, 6, 18, 9, 0, 0, tzinfo=timezone.utc),
    )


@pytest.mark.freeze_time("2026-06-18T09:30:00+00:00")
def test_push_usage_snapshots__never_reported_push_succeeds__saves_reported_until(
    organisation: Organisation,
    mocked_map_for_licensed_organisation: MagicMock,
) -> None:
    # Given - no UsageReportingState for the organisation

    # When
    push_usage_snapshots()

    # Then
    organisation.refresh_from_db()
    assert organisation.usage_reporting_state.reported_until == datetime(
        2026, 6, 18, 9, 0, 0, tzinfo=timezone.utc
    )


@pytest.mark.freeze_time("2026-06-18T09:30:00+00:00")
def test_push_usage_snapshots__previously_reported_push_succeeds__moves_reported_until(
    organisation: Organisation,
    mocked_map_for_licensed_organisation: MagicMock,
) -> None:
    # Given
    state = UsageReportingState.objects.create(
        organisation=organisation,
        reported_until=datetime(2026, 6, 15, 9, 0, 0, tzinfo=timezone.utc),
    )

    # When
    push_usage_snapshots()

    # Then
    state.refresh_from_db()
    assert state.reported_until == datetime(2026, 6, 18, 9, 0, 0, tzinfo=timezone.utc)


@pytest.mark.freeze_time("2026-06-18T09:30:00+00:00")
def test_push_usage_snapshots__already_reported_this_hour__skips_push(
    mocker: MockerFixture,
    log: StructuredLogCapture,
    organisation: Organisation,
    mocked_map_for_licensed_organisation: MagicMock,
) -> None:
    # Given - the window up to the start of the current hour is already reported
    UsageReportingState.objects.create(
        organisation=organisation,
        reported_until=datetime(2026, 6, 18, 9, 0, 0, tzinfo=timezone.utc),
    )
    mocked_push = mocker.patch("organisations.usage_reporting.services.push_snapshot")

    # When
    push_usage_snapshots()

    # Then
    mocked_push.assert_not_called()
    assert log.has("snapshot.skipped", level="debug", reason="empty_window")


@pytest.mark.freeze_time("2026-06-18T09:30:00+00:00")
def test_push_usage_snapshots__never_reported_push_fails__keeps_initial_boundary(
    mocker: MockerFixture,
    organisation: Organisation,
    mocked_map_for_licensed_organisation: MagicMock,
) -> None:
    # Given - no UsageReportingState for the organisation
    mocker.patch(
        "organisations.usage_reporting.services.push_snapshot",
        side_effect=requests.HTTPError("503 Server Error"),
    )

    # When
    push_usage_snapshots()

    # Then - the next run retries the window starting 24 hours ago
    organisation.refresh_from_db()
    assert organisation.usage_reporting_state.reported_until == datetime(
        2026, 6, 17, 9, 0, 0, tzinfo=timezone.utc
    )


@pytest.mark.freeze_time("2026-06-18T09:30:00+00:00")
def test_push_usage_snapshots__push_fails__keeps_reported_until(
    mocker: MockerFixture,
    log: StructuredLogCapture,
    organisation: Organisation,
    mocked_map_for_licensed_organisation: MagicMock,
) -> None:
    # Given
    reported_until = datetime(2026, 6, 15, 9, 0, 0, tzinfo=timezone.utc)
    state = UsageReportingState.objects.create(
        organisation=organisation, reported_until=reported_until
    )
    mocker.patch(
        "organisations.usage_reporting.services.push_snapshot",
        side_effect=requests.HTTPError("503 Server Error"),
    )

    # When
    push_usage_snapshots()

    # Then - the next run retries the same window
    state.refresh_from_db()
    assert state.reported_until == reported_until
    assert log.has("snapshot.errored", level="error")


def test_push_usage_snapshots__one_organisation_raises__continues(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    log: StructuredLogCapture,
    snapshot: UsageSnapshot,
) -> None:
    # Given
    settings.CONTROL_PLANE_URL = "https://cp.example.com"
    org_one = mocker.Mock(
        id=1,
        licence=mocker.Mock(signature="sig-1"),
        usage_reporting_state=mocker.Mock(reported_until=REPORTED_LONG_AGO),
    )
    org_two = mocker.Mock(
        id=2,
        licence=mocker.Mock(signature="sig-2"),
        usage_reporting_state=mocker.Mock(reported_until=REPORTED_LONG_AGO),
    )
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
