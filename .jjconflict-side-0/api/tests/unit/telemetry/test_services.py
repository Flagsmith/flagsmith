from datetime import datetime
from unittest.mock import Mock

from freezegun import freeze_time
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture
from requests_mock import Mocker as RequestsMocker

from app_analytics.dataclasses import UsageData
from telemetry.services import push_usage_snapshots

USAGE_URL = "https://cp.example.com/v1/public/usage"


def fake_usage_data(total: bool = False) -> UsageData:
    return UsageData(
        day=datetime.now(),
        flags=10,
        traits=10,
        identities=10,
        environment_document=10,
    )


def _make_organisation(
    mocker: MockerFixture, organisation_id: int, project_ids: list[int]
) -> Mock:
    organisation: Mock = mocker.Mock(
        id=organisation_id, num_seats=10, licence=mocker.Mock(signature="sig-1")
    )
    organisation.projects.all.return_value = [
        mocker.Mock(id=project_id) for project_id in project_ids
    ]
    return organisation


def _enable_telemetry(settings: SettingsWrapper) -> None:
    settings.ENABLE_TELEMETRY = True
    settings.CONTROL_PLANE_URL = "https://cp.example.com"


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
def test_push_usage_snapshots__licensed_organisation__pushes_snapshot(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    requests_mock: RequestsMocker,
    log: StructuredLogCapture,
) -> None:
    # Given
    _enable_telemetry(settings)
    org = mocker.Mock(id=1, num_seats=10, licence=mocker.Mock(signature="sig-1"))
    project = mocker.Mock(id=1)
    org.projects.all.return_value = [project]
    mocker.patch("telemetry.services.get_version", return_value="2.200.0")
    mocker.patch(
        "telemetry.services._get_licensed_organisations",
        return_value=[org],
    )
    mocker.patch(
        "telemetry.services.get_usage_data_for_window",
        return_value=[fake_usage_data()],
    )
    USAGE_ENDPOINT_PATH = "/v1/public/usage"
    url = f"{settings.CONTROL_PLANE_URL.rstrip('/')}{USAGE_ENDPOINT_PATH}"
    requests_mock.post(url, status_code=200)

    # When
    push_usage_snapshots()

    # Then
    assert log.events == [
        {
            "status_code": 200,
            "event": "snapshot.pushed",
            "organisation__id": 1,
            "level": "info",
        }
    ]
    assert requests_mock.last_request
    assert requests_mock.last_request.json() == {
        "timestamp": "2026-01-13T09:00:00Z",
        "seat_count": 10,
        "api_call_total": 40,
        "api_call_breakdown": {
            "flags": 10,
            "identities": 10,
            "traits": 10,
            "environment_documents": 10,
        },
        "project_count": 1,
        "instance_version": "2.200.0",
        "project_usage": [{"project_id": 1, "api_call_count": 40}],
    }


def test_push_usage_snapshots__control_plane_rejects__logs_push_failed(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    requests_mock: RequestsMocker,
    log: StructuredLogCapture,
) -> None:
    # Given
    _enable_telemetry(settings)
    mocker.patch(
        "telemetry.services._get_licensed_organisations",
        return_value=[_make_organisation(mocker, 1, [1])],
    )
    mocker.patch(
        "telemetry.services.get_usage_data_for_window",
        return_value=[fake_usage_data()],
    )
    requests_mock.post(USAGE_URL, status_code=500)

    # When
    push_usage_snapshots()

    # Then
    assert log.events == [
        {
            "status_code": 500,
            "event": "snapshot.push_failed",
            "organisation__id": 1,
            "level": "warning",
        }
    ]


def test_push_usage_snapshots__one_organisation_errors__logs_error_and_pushes_others(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    requests_mock: RequestsMocker,
    log: StructuredLogCapture,
) -> None:
    # Given
    _enable_telemetry(settings)
    mocker.patch(
        "telemetry.services._get_licensed_organisations",
        return_value=[
            _make_organisation(mocker, 1, [1]),
            _make_organisation(mocker, 2, [2]),
        ],
    )

    def get_usage_data_for_window(
        organisation: Mock, *args: object, **kwargs: object
    ) -> list[UsageData]:
        if organisation.id == 1:
            raise RuntimeError("Analytics database unavailable")
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
            "organisation__id": 1,
            "level": "error",
            "exc_info": True,
        },
        {
            "status_code": 200,
            "event": "snapshot.pushed",
            "organisation__id": 2,
            "level": "info",
        },
    ]


def test_push_usage_snapshots__more_projects_than_row_cap__sends_highest_usage_only(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    requests_mock: RequestsMocker,
) -> None:
    # Given
    _enable_telemetry(settings)
    mocker.patch("telemetry.services.MAX_PROJECT_USAGE_ROWS", 1)
    mocker.patch(
        "telemetry.services._get_licensed_organisations",
        return_value=[_make_organisation(mocker, 1, [1, 2])],
    )
    flags_by_project_id = {None: 10, 1: 3, 2: 7}

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
    assert body["project_usage"] == [{"project_id": 2, "api_call_count": 7}]


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
