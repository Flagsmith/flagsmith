from datetime import datetime, timezone

from freezegun import freeze_time
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture
from requests_mock import Mocker as RequestsMocker

from app_analytics.dataclasses import UsageData
from organisations.models import Organisation
from projects.models import Project
from telemetry.models import UsageReportingState
from telemetry.services import push_usage_snapshots

USAGE_URL = "https://cp.example.com/v1/public/usage"
WINDOW_END = datetime(2026, 1, 14, 9, tzinfo=timezone.utc)


def fake_usage_data() -> UsageData:
    return UsageData(
        day=datetime.now(),
        flags=10,
        traits=10,
        identities=10,
        environment_document=10,
    )


def _enable_telemetry(settings: SettingsWrapper) -> None:
    settings.ENABLE_TELEMETRY = True
    settings.CONTROL_PLANE_URL = "https://cp.example.com"


def _license_organisations(mocker: MockerFixture, *organisations: Organisation) -> None:
    mocker.patch.object(
        Organisation,
        "licence",
        new_callable=mocker.PropertyMock,
        return_value=mocker.Mock(signature="sig-1"),
        create=True,
    )
    mocker.patch(
        "telemetry.services._get_licensed_organisations",
        return_value=list(organisations),
    )


def test_push_usage_snapshots__no_telemetry__no_op(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    log: StructuredLogCapture,
) -> None:
    # Given
    settings.ENABLE_TELEMETRY = False
    mocked_post = mocker.patch("telemetry.services.post_usage_snapshot")

    # When
    push_usage_snapshots()

    # Then
    mocked_post.assert_not_called()
    assert log.events == [
        {"event": "run.skipped", "level": "debug", "reason": "telemetry_disabled"}
    ]


def test_push_usage_snapshots__url_unset__no_op(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    log: StructuredLogCapture,
) -> None:
    # Given
    settings.ENABLE_TELEMETRY = True
    settings.CONTROL_PLANE_URL = None
    mocked_post = mocker.patch("telemetry.services.post_usage_snapshot")

    # When
    push_usage_snapshots()

    # Then
    mocked_post.assert_not_called()
    assert log.events == [
        {"event": "run.skipped", "level": "debug", "reason": "control_plane_url_unset"}
    ]


def test_push_usage_snapshots__no_licensed_organisations__no_op(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    log: StructuredLogCapture,
) -> None:
    # Given
    _enable_telemetry(settings)
    mocked_post = mocker.patch("telemetry.services.post_usage_snapshot")
    mocker.patch("telemetry.services._get_licensed_organisations", return_value=[])

    # When
    push_usage_snapshots()

    # Then
    mocked_post.assert_not_called()
    assert log.events == [
        {
            "event": "run.skipped",
            "level": "debug",
            "reason": "no_licensed_organisations",
        }
    ]


@freeze_time("2026-01-14T09:30:00Z")
def test_push_usage_snapshots__first_push__sends_last_24_hours_and_records_state(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    requests_mock: RequestsMocker,
    log: StructuredLogCapture,
    organisation: Organisation,
    project: Project,
) -> None:
    # Given
    _enable_telemetry(settings)
    _license_organisations(mocker, organisation)
    mocker.patch("telemetry.services.get_version", return_value="2.200.0")
    mocker.patch(
        "telemetry.services.get_usage_data_for_window",
        return_value=[fake_usage_data()],
    )
    requests_mock.post(USAGE_URL, status_code=200)

    # When
    push_usage_snapshots()

    # Then
    assert log.events == [
        {
            "status_code": 200,
            "event": "snapshot.pushed",
            "organisation__id": organisation.id,
            "level": "info",
        }
    ]
    assert requests_mock.last_request
    assert requests_mock.last_request.json() == {
        "timestamp": "2026-01-13T09:00:00Z",
        "seat_count": 2,
        "api_call_total": 40,
        "api_call_breakdown": {
            "flags": 10,
            "identities": 10,
            "traits": 10,
            "environment_documents": 10,
        },
        "project_count": 1,
        "instance_version": "2.200.0",
        "project_usage": [{"project_id": project.id, "api_call_count": 40}],
    }
    state = UsageReportingState.objects.get(organisation=organisation)
    assert state.reported_until == WINDOW_END


@freeze_time("2026-01-14T09:30:00Z")
def test_push_usage_snapshots__previous_push_missed__sends_from_last_reported(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    requests_mock: RequestsMocker,
    organisation: Organisation,
) -> None:
    # Given
    _enable_telemetry(settings)
    _license_organisations(mocker, organisation)
    reported_until = datetime(2026, 1, 11, 9, tzinfo=timezone.utc)
    UsageReportingState.objects.create(
        organisation=organisation, reported_until=reported_until
    )
    get_usage_data_for_window = mocker.patch(
        "telemetry.services.get_usage_data_for_window",
        return_value=[fake_usage_data()],
    )
    requests_mock.post(USAGE_URL, status_code=200)

    # When
    push_usage_snapshots()

    # Then
    get_usage_data_for_window.assert_called_once_with(
        organisation, reported_until, WINDOW_END
    )
    assert requests_mock.last_request
    assert requests_mock.last_request.json()["timestamp"] == "2026-01-11T09:00:00Z"
    state = UsageReportingState.objects.get(organisation=organisation)
    assert state.reported_until == WINDOW_END


@freeze_time("2026-01-14T09:30:00Z")
def test_push_usage_snapshots__window_already_reported__skips_organisation(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    requests_mock: RequestsMocker,
    log: StructuredLogCapture,
    organisation: Organisation,
) -> None:
    # Given
    _enable_telemetry(settings)
    _license_organisations(mocker, organisation)
    UsageReportingState.objects.create(
        organisation=organisation, reported_until=WINDOW_END
    )

    # When
    push_usage_snapshots()

    # Then
    assert not requests_mock.called
    assert log.events == [
        {
            "event": "snapshot.skipped",
            "organisation__id": organisation.id,
            "level": "debug",
            "reason": "empty_window",
        }
    ]


@freeze_time("2026-01-14T09:30:00Z")
def test_push_usage_snapshots__control_plane_rejects__logs_error_and_keeps_state(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    requests_mock: RequestsMocker,
    log: StructuredLogCapture,
    organisation: Organisation,
) -> None:
    # Given
    _enable_telemetry(settings)
    _license_organisations(mocker, organisation)
    mocker.patch(
        "telemetry.services.get_usage_data_for_window",
        return_value=[fake_usage_data()],
    )
    requests_mock.post(USAGE_URL, status_code=500)

    # When
    push_usage_snapshots()

    # Then
    [event] = log.events
    reason = event.pop("reason")
    assert event == {
        "event": "snapshot.errored",
        "organisation__id": organisation.id,
        "level": "error",
        "exc_info": True,
    }
    assert "500 Server Error" in str(reason)
    state = UsageReportingState.objects.get(organisation=organisation)
    assert state.reported_until == datetime(2026, 1, 13, 9, tzinfo=timezone.utc)


def test_push_usage_snapshots__one_organisation_errors__logs_error_and_pushes_others(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    requests_mock: RequestsMocker,
    log: StructuredLogCapture,
    organisation: Organisation,
) -> None:
    # Given
    _enable_telemetry(settings)
    other_organisation = Organisation.objects.create(name="Other Org")
    _license_organisations(mocker, organisation, other_organisation)
    error = RuntimeError("Analytics database unavailable")

    def get_usage_data_for_window(
        usage_organisation: Organisation, *args: object, **kwargs: object
    ) -> list[UsageData]:
        if usage_organisation == organisation:
            raise error
        return [fake_usage_data()]

    mocker.patch(
        "telemetry.services.get_usage_data_for_window",
        side_effect=get_usage_data_for_window,
    )
    requests_mock.post(USAGE_URL, status_code=200)

    # When
    push_usage_snapshots()

    # Then
    assert requests_mock.call_count == 1
    assert log.events == [
        {
            "event": "snapshot.errored",
            "organisation__id": organisation.id,
            "level": "error",
            "exc_info": True,
            "reason": error,
        },
        {
            "status_code": 200,
            "event": "snapshot.pushed",
            "organisation__id": other_organisation.id,
            "level": "info",
        },
    ]


def test_push_usage_snapshots__more_projects_than_row_cap__sends_highest_usage_only(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    requests_mock: RequestsMocker,
    organisation: Organisation,
    project: Project,
    project_b: Project,
) -> None:
    # Given
    _enable_telemetry(settings)
    mocker.patch("telemetry.services.MAX_PROJECT_USAGE_ROWS", 1)
    _license_organisations(mocker, organisation)
    flags_by_project_id = {None: 10, project.id: 3, project_b.id: 7}

    def get_usage_data_for_window(
        *args: object, project_id: int | None = None
    ) -> list[UsageData]:
        return [UsageData(day=datetime.now(), flags=flags_by_project_id[project_id])]

    mocker.patch(
        "telemetry.services.get_usage_data_for_window",
        side_effect=get_usage_data_for_window,
    )
    requests_mock.post(USAGE_URL, status_code=200)

    # When
    push_usage_snapshots()

    # Then
    assert requests_mock.last_request
    body = requests_mock.last_request.json()
    assert body["project_count"] == 2
    assert body["project_usage"] == [{"project_id": project_b.id, "api_call_count": 7}]


def test_push_usage_snapshots__licensing_not_installed__skips_run(
    settings: SettingsWrapper,
    requests_mock: RequestsMocker,
    log: StructuredLogCapture,
) -> None:
    # Given
    _enable_telemetry(settings)
    settings.LICENSING_INSTALLED = False

    # When
    push_usage_snapshots()

    # Then
    assert not requests_mock.called
    assert log.events == [
        {
            "event": "run.skipped",
            "level": "debug",
            "reason": "no_licensed_organisations",
        }
    ]
