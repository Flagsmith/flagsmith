import datetime

import pytest
from django.contrib import messages
from django.contrib.admin.sites import AdminSite
from django.http import HttpRequest
from django.test import RequestFactory
from freezegun import freeze_time
from pytest_mock import MockerFixture

from integrations.launch_darkly.admin import LaunchDarklyImportRequestAdmin
from integrations.launch_darkly.models import (
    LaunchDarklyImportRequest,
    LaunchDarklyImportStatus,
)

FROZEN_NOW = datetime.datetime(2026, 4, 23, 10, 0, 0, tzinfo=datetime.timezone.utc)
EXISTING_COMPLETED_AT = datetime.datetime(
    2026, 4, 1, 9, 0, 0, tzinfo=datetime.timezone.utc
)
PENDING_STATUS: LaunchDarklyImportStatus = {
    "requested_environment_count": 2,
    "requested_flag_count": 5,
    "error_messages": [],
}


@pytest.fixture
def ld_admin() -> LaunchDarklyImportRequestAdmin:
    return LaunchDarklyImportRequestAdmin(LaunchDarklyImportRequest, AdminSite())


@pytest.fixture
def ld_admin_request(rf: RequestFactory) -> HttpRequest:
    return rf.get("/admin/launch_darkly/launchdarklyimportrequest/")


def test_launch_darkly_import_request_admin__has_add_permission__returns_false(
    ld_admin: LaunchDarklyImportRequestAdmin,
    ld_admin_request: HttpRequest,
) -> None:
    # Given / When
    has_add = ld_admin.has_add_permission(ld_admin_request)

    # Then
    assert has_add is False


@pytest.mark.parametrize(
    "status, expected",
    [
        pytest.param(PENDING_STATUS, "pending", id="no-result-key"),
        pytest.param({**PENDING_STATUS, "result": "success"}, "success", id="success"),
        pytest.param({**PENDING_STATUS, "result": "failure"}, "failure", id="failure"),
        pytest.param(
            {**PENDING_STATUS, "result": "incomplete"}, "incomplete", id="incomplete"
        ),
    ],
)
def test_launch_darkly_import_request_admin__result__returns_expected(
    ld_admin: LaunchDarklyImportRequestAdmin,
    import_request: LaunchDarklyImportRequest,
    status: LaunchDarklyImportStatus,
    expected: str,
) -> None:
    # Given
    import_request.status = status

    # When
    displayed = ld_admin.result(import_request)

    # Then
    assert displayed == expected


@freeze_time(FROZEN_NOW)
@pytest.mark.parametrize(
    "initial_status, initial_completed_at, expected_status, expected_completed_at, expected_message",
    [
        pytest.param(
            PENDING_STATUS,
            None,
            {**PENDING_STATUS, "result": "failure"},
            FROZEN_NOW,
            "Marked 1 import(s) as failed; skipped 0 already-resolved import(s).",
            id="pending-no-completed-at-marked-and-completed-now",
        ),
        pytest.param(
            PENDING_STATUS,
            EXISTING_COMPLETED_AT,
            {**PENDING_STATUS, "result": "failure"},
            EXISTING_COMPLETED_AT,
            "Marked 1 import(s) as failed; skipped 0 already-resolved import(s).",
            id="pending-with-completed-at-marked-and-completed-at-preserved",
        ),
        pytest.param(
            {**PENDING_STATUS, "result": "success"},
            EXISTING_COMPLETED_AT,
            {**PENDING_STATUS, "result": "success"},
            EXISTING_COMPLETED_AT,
            "Marked 0 import(s) as failed; skipped 1 already-resolved import(s).",
            id="already-resolved-skipped",
        ),
    ],
)
def test_launch_darkly_import_request_admin__mark_as_failure__expected(
    ld_admin: LaunchDarklyImportRequestAdmin,
    ld_admin_request: HttpRequest,
    import_request: LaunchDarklyImportRequest,
    mocker: MockerFixture,
    initial_status: LaunchDarklyImportStatus,
    initial_completed_at: datetime.datetime | None,
    expected_status: LaunchDarklyImportStatus,
    expected_completed_at: datetime.datetime,
    expected_message: str,
) -> None:
    # Given
    import_request.status = initial_status
    import_request.completed_at = initial_completed_at
    import_request.save()
    message_user_mock = mocker.patch.object(ld_admin, "message_user")
    queryset = LaunchDarklyImportRequest.objects.filter(pk=import_request.pk)

    # When
    ld_admin.mark_as_failure(ld_admin_request, queryset)

    # Then
    import_request.refresh_from_db()
    assert import_request.status == expected_status
    assert import_request.completed_at == expected_completed_at
    message_user_mock.assert_called_once_with(
        ld_admin_request,
        expected_message,
        messages.SUCCESS,
    )
