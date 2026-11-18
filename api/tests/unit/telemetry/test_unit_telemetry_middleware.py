import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from opentelemetry.trace import Span
from pytest_django import DjangoAssertNumQueries
from pytest_structlog import StructuredLogCapture
from rest_framework.test import APIClient

from api_keys.models import MasterAPIKey
from api_keys.user import APIKeyUser
from environments.models import Environment
from organisations.models import Organisation, OrganisationRole
from telemetry.middleware import CLIUsageLoggerMiddleware
from users.models import FFAdminUser

CLI_USER_AGENT = "flagsmith-cli/2.0.0 (darwin/arm64)"


@pytest.mark.usefixtures("organisation")
def test_mcp_usage_logger_middleware__no_mcp_baggage__logs_nothing(
    staff_client: APIClient,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    response = staff_client.get("/api/v1/projects/")

    # Then
    assert response.status_code == 200
    assert log.events == []


@pytest.mark.usefixtures("mcp_baggage", "recording_span", "organisation")
def test_mcp_usage_logger_middleware__organisation_id_span_attribute__logs_span_organisation_id(
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
def test_mcp_usage_logger_middleware__user_with_single_organisation__logs_user_organisation_id(
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
def test_mcp_usage_logger_middleware__user_without_organisations__logs_warning(
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
def test_mcp_usage_logger_middleware__user_with_multiple_organisations__logs_warning(
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
def test_mcp_usage_logger_middleware__unauthenticated_request__logs_nothing(
    api_client: APIClient,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    response = api_client.get("/api/v1/projects/")

    # Then
    assert response.status_code == 401
    assert log.events == []


@pytest.mark.usefixtures("mcp_baggage")
def test_mcp_usage_logger_middleware__error_response__logs_error_status(
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
def test_mcp_usage_logger_middleware__sdk_request__logs_nothing(
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
def test_cli_usage_logger_middleware__non_cli_request__logs_nothing(
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
def test_cli_usage_logger_middleware__user_agent_not_matching_cli_pattern__logs_nothing(
    staff_client: APIClient,
    log: StructuredLogCapture,
    user_agent: str,
) -> None:
    # Given / When
    response = staff_client.get("/api/v1/projects/", HTTP_USER_AGENT=user_agent)

    # Then
    assert response.status_code == 200
    assert log.events == []


def test_cli_usage_logger_middleware__user_with_single_organisation__logs_event(
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
            "event": "cli.request.made",
            "cli__version": "2.0.0",
            "cli__os": "darwin",
            "cli__arch": "arm64",
            "organisation__id": organisation.pk,
            "status": "success",
            "amplitude__user_id": str(staff_user.uuid),
        }
    ]


@pytest.mark.usefixtures("recording_span", "organisation")
def test_cli_usage_logger_middleware__organisation_id_span_attribute__logs_span_organisation_id(
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
            "event": "cli.request.made",
            "cli__version": "2.0.0",
            "cli__os": "darwin",
            "cli__arch": "arm64",
            "organisation__id": other_organisation.pk,
            "status": "success",
            "amplitude__user_id": str(staff_user.uuid),
        }
    ]


@pytest.mark.usefixtures("organisation")
def test_cli_usage_logger_middleware__user_with_multiple_organisations__logs_event_without_organisation_id(
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
            "level": "info",
            "event": "cli.request.made",
            "cli__version": "2.0.0",
            "cli__os": "darwin",
            "cli__arch": "arm64",
            "status": "success",
            "amplitude__user_id": str(staff_user.uuid),
        }
    ]


def test_cli_usage_logger_middleware__user_without_organisations__logs_event_without_organisation_id(
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
            "level": "info",
            "event": "cli.request.made",
            "cli__version": "2.0.0",
            "cli__os": "darwin",
            "cli__arch": "arm64",
            "status": "success",
            "amplitude__user_id": str(staff_user.uuid),
        }
    ]


def test_cli_usage_logger_middleware__master_api_key__logs_key_organisation_id_without_user_id(
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
            "event": "cli.request.made",
            "cli__version": "2.0.0",
            "cli__os": "darwin",
            "cli__arch": "arm64",
            "organisation__id": organisation.pk,
            "status": "success",
        }
    ]


def test_cli_usage_logger_middleware__unauthenticated_request__logs_nothing(
    api_client: APIClient,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    response = api_client.get("/api/v1/projects/", HTTP_USER_AGENT=CLI_USER_AGENT)

    # Then
    assert response.status_code == 401
    assert log.events == []


def test_cli_usage_logger_middleware__error_response__logs_error_status(
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
            "event": "cli.request.made",
            "cli__version": "2.0.0",
            "cli__os": "darwin",
            "cli__arch": "arm64",
            "organisation__id": organisation.pk,
            "status": "error",
            "amplitude__user_id": str(staff_user.uuid),
        }
    ]


def test_cli_usage_logger_middleware__server_error_response__logs_error_status(
    rf: RequestFactory,
    staff_user: FFAdminUser,
    organisation: Organisation,
    log: StructuredLogCapture,
) -> None:
    # Given
    request = rf.get("/api/v1/projects/", HTTP_USER_AGENT=CLI_USER_AGENT)
    request.user = staff_user
    middleware = CLIUsageLoggerMiddleware(lambda request: HttpResponse(status=500))

    # When
    response = middleware(request)

    # Then
    assert response.status_code == 500
    assert log.events == [
        {
            "level": "info",
            "event": "cli.request.made",
            "cli__version": "2.0.0",
            "cli__os": "darwin",
            "cli__arch": "arm64",
            "organisation__id": organisation.pk,
            "status": "error",
            "amplitude__user_id": str(staff_user.uuid),
        }
    ]


@pytest.mark.parametrize(
    "user_agent, expected_version, expected_os, expected_arch",
    [
        ("flagsmith-cli/2.0.0-beta.3 (linux/amd64)", "2.0.0-beta.3", "linux", "amd64"),
        ("flagsmith-cli/dev (windows/386)", "dev", "windows", "386"),
        ("flagsmith-cli/99.0.0 (freebsd/riscv64)", "99.0.0", "freebsd", "riscv64"),
    ],
)
def test_cli_usage_logger_middleware__cli_user_agent__passes_version_through_unchanged(
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
            "event": "cli.request.made",
            "cli__version": expected_version,
            "cli__os": expected_os,
            "cli__arch": expected_arch,
            "organisation__id": organisation.pk,
            "status": "success",
            "amplitude__user_id": str(staff_user.uuid),
        }
    ]


def test_cli_usage_logger_middleware__organisation_id_span_attribute__does_not_query_database(
    rf: RequestFactory,
    staff_user: FFAdminUser,
    organisation: Organisation,
    recording_span: Span,
    log: StructuredLogCapture,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    # Given
    recording_span.set_attribute("organisation.id", organisation.pk)
    request = rf.get("/api/v1/projects/", HTTP_USER_AGENT=CLI_USER_AGENT)
    request.user = staff_user
    middleware = CLIUsageLoggerMiddleware(lambda request: HttpResponse(status=200))

    # When
    with django_assert_num_queries(0):
        middleware(request)

    # Then
    assert log.events == [
        {
            "level": "info",
            "event": "cli.request.made",
            "cli__version": "2.0.0",
            "cli__os": "darwin",
            "cli__arch": "arm64",
            "organisation__id": organisation.pk,
            "status": "success",
            "amplitude__user_id": str(staff_user.uuid),
        }
    ]


def test_cli_usage_logger_middleware__master_api_key__does_not_query_database(
    rf: RequestFactory,
    admin_master_api_key_object: MasterAPIKey,
    organisation: Organisation,
    log: StructuredLogCapture,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    # Given
    request = rf.get("/api/v1/projects/", HTTP_USER_AGENT=CLI_USER_AGENT)
    request.user = APIKeyUser(admin_master_api_key_object)  # type: ignore[assignment]
    middleware = CLIUsageLoggerMiddleware(lambda request: HttpResponse(status=200))

    # When
    with django_assert_num_queries(0):
        middleware(request)

    # Then
    assert log.events == [
        {
            "level": "info",
            "event": "cli.request.made",
            "cli__version": "2.0.0",
            "cli__os": "darwin",
            "cli__arch": "arm64",
            "organisation__id": organisation.pk,
            "status": "success",
        }
    ]
