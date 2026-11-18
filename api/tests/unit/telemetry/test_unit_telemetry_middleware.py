import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from pytest_structlog import StructuredLogCapture
from rest_framework.test import APIClient

from environments.models import Environment
from organisations.models import Organisation, OrganisationRole
from telemetry.middleware import ClientUsageLoggerMiddleware
from users.models import FFAdminUser

CLI_USER_AGENT = "flagsmith-cli/2.0.0 (darwin/arm64)"


@pytest.mark.usefixtures("organisation")
def test_client_usage_logger_middleware__no_mcp_baggage__logs_nothing(
    staff_client: APIClient,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    response = staff_client.get("/api/v1/projects/")

    # Then
    assert response.status_code == 200
    assert log.events == []


@pytest.mark.usefixtures("mcp_baggage", "recording_span", "organisation")
def test_client_usage_logger_middleware__mcp_organisation_id_span_attribute__logs_span_organisation_id(
    staff_client: APIClient,
    staff_user: FFAdminUser,
    log: StructuredLogCapture,
) -> None:
    # Given
    other_organisation = Organisation.objects.create(name="Other Org")
    staff_user.add_organisation(other_organisation, role=OrganisationRole.ADMIN)

    # When
    response = staff_client.get(
        f"/api/v1/organisations/{other_organisation.pk}/invites/"
    )

    # Then
    assert response.status_code == 200
    assert log.events == [
        {
            "level": "info",
            "event": "tool.called",
            "organisation__id": other_organisation.pk,
            "status": "success",
        }
    ]


@pytest.mark.usefixtures("mcp_baggage")
def test_client_usage_logger_middleware__mcp_user_with_single_organisation__logs_user_organisation_id(
    staff_client: APIClient,
    organisation: Organisation,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    response = staff_client.get("/api/v1/projects/")

    # Then
    assert response.status_code == 200
    assert log.events == [
        {
            "level": "info",
            "event": "tool.called",
            "organisation__id": organisation.pk,
            "status": "success",
        }
    ]


@pytest.mark.usefixtures("mcp_baggage")
def test_client_usage_logger_middleware__mcp_user_without_organisations__logs_warning(
    staff_client: APIClient,
    staff_user: FFAdminUser,
    log: StructuredLogCapture,
) -> None:
    # Given
    assert not staff_user.organisations.exists()

    # When
    response = staff_client.get("/api/v1/projects/")

    # Then
    assert response.status_code == 200
    assert log.events == [
        {
            "level": "warning",
            "event": "tool.called",
            "organisation__id": None,
            "status": "success",
        }
    ]


@pytest.mark.usefixtures("mcp_baggage", "organisation")
def test_client_usage_logger_middleware__mcp_user_with_multiple_organisations__logs_warning(
    staff_client: APIClient,
    staff_user: FFAdminUser,
    log: StructuredLogCapture,
) -> None:
    # Given
    other_organisation = Organisation.objects.create(name="Other Org")
    staff_user.add_organisation(other_organisation, role=OrganisationRole.USER)

    # When
    response = staff_client.get("/api/v1/projects/")

    # Then
    assert response.status_code == 200
    assert log.events == [
        {
            "level": "warning",
            "event": "tool.called",
            "organisation__id": None,
            "status": "success",
        }
    ]


@pytest.mark.usefixtures("mcp_baggage")
def test_client_usage_logger_middleware__mcp_unauthenticated_request__logs_nothing(
    api_client: APIClient,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    response = api_client.get("/api/v1/projects/")

    # Then
    assert response.status_code == 401
    assert log.events == []


@pytest.mark.usefixtures("mcp_baggage")
def test_client_usage_logger_middleware__mcp_error_response__logs_error_status(
    staff_client: APIClient,
    organisation: Organisation,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    response = staff_client.get(f"/api/v1/organisations/{organisation.pk}/invites/")

    # Then
    assert response.status_code == 403
    assert log.events == [
        {
            "level": "info",
            "event": "tool.called",
            "organisation__id": organisation.pk,
            "status": "error",
        }
    ]


@pytest.mark.usefixtures("mcp_baggage")
def test_client_usage_logger_middleware__mcp_sdk_request__logs_nothing(
    api_client: APIClient,
    environment: Environment,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    response = api_client.get(
        "/api/v1/flags/",
        HTTP_X_ENVIRONMENT_KEY=environment.api_key,
    )

    # Then
    assert response.status_code == 200
    assert log.events == []


@pytest.mark.usefixtures("organisation")
def test_client_usage_logger_middleware__no_cli_user_agent__logs_nothing(
    staff_client: APIClient,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    response = staff_client.get("/api/v1/projects/")

    # Then
    assert response.status_code == 200
    assert log.events == []


@pytest.mark.parametrize(
    "user_agent",
    [
        "python-requests/2.32.3",
        "flagsmith-mcp/1.0.0 (linux/amd64)",
        "flagsmith-python-sdk/5.0.0",
        "flagsmith-cli",
        "flagsmith-cli/2.0.0",
        "flagsmith-cli/2.0.0 (darwin)",
        "flagsmith-cli/ (darwin/arm64)",
        "not-flagsmith-cli/2.0.0 (darwin/arm64)",
        "Mozilla/5.0 flagsmith-cli/2.0.0 (darwin/arm64)",
    ],
)
@pytest.mark.usefixtures("organisation")
def test_client_usage_logger_middleware__user_agent_not_matching_cli_pattern__logs_nothing(
    staff_client: APIClient,
    log: StructuredLogCapture,
    user_agent: str,
) -> None:
    # Given / When
    response = staff_client.get("/api/v1/projects/", HTTP_USER_AGENT=user_agent)

    # Then
    assert response.status_code == 200
    assert log.events == []


@pytest.mark.usefixtures("recording_span", "organisation")
def test_client_usage_logger_middleware__cli_organisation_id_span_attribute__logs_span_organisation_id(
    staff_client: APIClient,
    staff_user: FFAdminUser,
    log: StructuredLogCapture,
) -> None:
    # Given
    other_organisation = Organisation.objects.create(name="Other Org")
    staff_user.add_organisation(other_organisation, role=OrganisationRole.ADMIN)

    # When
    response = staff_client.get(
        f"/api/v1/organisations/{other_organisation.pk}/invites/",
        HTTP_USER_AGENT=CLI_USER_AGENT,
    )

    # Then
    assert response.status_code == 200
    assert log.events == [
        {
            "level": "info",
            "event": "request.made",
            "cli__version": "2.0.0",
            "cli__os": "darwin",
            "cli__arch": "arm64",
            "organisation__id": other_organisation.pk,
            "status": "success",
            "amplitude__user_id": str(staff_user.uuid),
        }
    ]


def test_client_usage_logger_middleware__cli_user_with_single_organisation__logs_user_organisation_id(
    staff_client: APIClient,
    staff_user: FFAdminUser,
    organisation: Organisation,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    response = staff_client.get("/api/v1/projects/", HTTP_USER_AGENT=CLI_USER_AGENT)

    # Then
    assert response.status_code == 200
    assert log.events == [
        {
            "level": "info",
            "event": "request.made",
            "cli__version": "2.0.0",
            "cli__os": "darwin",
            "cli__arch": "arm64",
            "organisation__id": organisation.pk,
            "status": "success",
            "amplitude__user_id": str(staff_user.uuid),
        }
    ]


def test_client_usage_logger_middleware__cli_user_without_organisations__logs_warning(
    staff_client: APIClient,
    staff_user: FFAdminUser,
    log: StructuredLogCapture,
) -> None:
    # Given
    assert not staff_user.organisations.exists()

    # When
    response = staff_client.get("/api/v1/projects/", HTTP_USER_AGENT=CLI_USER_AGENT)

    # Then
    assert response.status_code == 200
    assert log.events == [
        {
            "level": "warning",
            "event": "request.made",
            "cli__version": "2.0.0",
            "cli__os": "darwin",
            "cli__arch": "arm64",
            "organisation__id": None,
            "status": "success",
            "amplitude__user_id": str(staff_user.uuid),
        }
    ]


@pytest.mark.usefixtures("organisation")
def test_client_usage_logger_middleware__cli_user_with_multiple_organisations__logs_warning(
    staff_client: APIClient,
    staff_user: FFAdminUser,
    log: StructuredLogCapture,
) -> None:
    # Given
    other_organisation = Organisation.objects.create(name="Other Org")
    staff_user.add_organisation(other_organisation, role=OrganisationRole.USER)

    # When
    response = staff_client.get("/api/v1/projects/", HTTP_USER_AGENT=CLI_USER_AGENT)

    # Then
    assert response.status_code == 200
    assert log.events == [
        {
            "level": "warning",
            "event": "request.made",
            "cli__version": "2.0.0",
            "cli__os": "darwin",
            "cli__arch": "arm64",
            "organisation__id": None,
            "status": "success",
            "amplitude__user_id": str(staff_user.uuid),
        }
    ]


def test_client_usage_logger_middleware__cli_master_api_key__logs_key_organisation_id(
    admin_master_api_key_client: APIClient,
    organisation: Organisation,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    response = admin_master_api_key_client.get(
        "/api/v1/projects/",
        HTTP_USER_AGENT=CLI_USER_AGENT,
    )

    # Then
    assert response.status_code == 200
    assert log.events == [
        {
            "level": "info",
            "event": "request.made",
            "cli__version": "2.0.0",
            "cli__os": "darwin",
            "cli__arch": "arm64",
            "organisation__id": organisation.pk,
            "status": "success",
        }
    ]


def test_client_usage_logger_middleware__cli_unauthenticated_request__logs_nothing(
    api_client: APIClient,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    response = api_client.get("/api/v1/projects/", HTTP_USER_AGENT=CLI_USER_AGENT)

    # Then
    assert response.status_code == 401
    assert log.events == []


def test_client_usage_logger_middleware__cli_error_response__logs_error_status(
    staff_client: APIClient,
    staff_user: FFAdminUser,
    organisation: Organisation,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    response = staff_client.get(
        f"/api/v1/organisations/{organisation.pk}/invites/",
        HTTP_USER_AGENT=CLI_USER_AGENT,
    )

    # Then
    assert response.status_code == 403
    assert log.events == [
        {
            "level": "info",
            "event": "request.made",
            "cli__version": "2.0.0",
            "cli__os": "darwin",
            "cli__arch": "arm64",
            "organisation__id": organisation.pk,
            "status": "error",
            "amplitude__user_id": str(staff_user.uuid),
        }
    ]


def test_client_usage_logger_middleware__cli_server_error_response__logs_error_status(
    rf: RequestFactory,
    staff_user: FFAdminUser,
    organisation: Organisation,
    log: StructuredLogCapture,
) -> None:
    # Given
    request = rf.get("/api/v1/projects/", HTTP_USER_AGENT=CLI_USER_AGENT)
    request.user = staff_user
    middleware = ClientUsageLoggerMiddleware(lambda request: HttpResponse(status=500))

    # When
    response = middleware(request)

    # Then
    assert response.status_code == 500
    assert log.events == [
        {
            "level": "info",
            "event": "request.made",
            "cli__version": "2.0.0",
            "cli__os": "darwin",
            "cli__arch": "arm64",
            "organisation__id": organisation.pk,
            "status": "error",
            "amplitude__user_id": str(staff_user.uuid),
        }
    ]


def test_client_usage_logger_middleware__cli_sdk_request__logs_nothing(
    api_client: APIClient,
    environment: Environment,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    response = api_client.get(
        "/api/v1/flags/",
        HTTP_X_ENVIRONMENT_KEY=environment.api_key,
        HTTP_USER_AGENT=CLI_USER_AGENT,
    )

    # Then
    assert response.status_code == 200
    assert log.events == []


@pytest.mark.parametrize(
    "user_agent, expected_version, expected_os, expected_arch",
    [
        ("flagsmith-cli/2.0.0-beta.3 (linux/amd64)", "2.0.0-beta.3", "linux", "amd64"),
        ("flagsmith-cli/dev (windows/386)", "dev", "windows", "386"),
        ("flagsmith-cli/99.0.0 (freebsd/riscv64)", "99.0.0", "freebsd", "riscv64"),
    ],
)
def test_client_usage_logger_middleware__cli_user_agent__passes_version_through_unchanged(
    staff_client: APIClient,
    staff_user: FFAdminUser,
    organisation: Organisation,
    log: StructuredLogCapture,
    user_agent: str,
    expected_version: str,
    expected_os: str,
    expected_arch: str,
) -> None:
    # Given / When
    response = staff_client.get("/api/v1/projects/", HTTP_USER_AGENT=user_agent)

    # Then
    assert response.status_code == 200
    assert log.events == [
        {
            "level": "info",
            "event": "request.made",
            "cli__version": expected_version,
            "cli__os": expected_os,
            "cli__arch": expected_arch,
            "organisation__id": organisation.pk,
            "status": "success",
            "amplitude__user_id": str(staff_user.uuid),
        }
    ]
