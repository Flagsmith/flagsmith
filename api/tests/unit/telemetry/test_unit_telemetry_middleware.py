import pytest
from django.http import HttpRequest, HttpResponse
from pytest_django import DjangoAssertNumQueries
from pytest_structlog import StructuredLogCapture
from rest_framework.test import APIClient

from api_keys.user import APIKeyUser
from environments.models import Environment
from organisations.models import Organisation, OrganisationRole
from telemetry.middleware import CLIUsageLoggerMiddleware
from telemetry.spans import set_span_attribute
from users.models import FFAdminUser


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


@pytest.mark.usefixtures("recording_span")
def test_cli_usage_logger_middleware__authenticated_cli_request__logs_usage_event(
    staff_client: APIClient,
    staff_user: FFAdminUser,
    organisation: Organisation,
    log: StructuredLogCapture,
) -> None:
    # Given
    set_span_attribute("organisation.id", organisation.pk)

    # When
    response = staff_client.get(
        "/api/v1/projects/",
        HTTP_USER_AGENT="flagsmith-cli/2.0.0-beta.3 (darwin/arm64)",
    )

    # Then
    assert response.status_code == 200
    assert log.events == [
        {
            "level": "info",
            "event": "request.made",
            "cli__version": "2.0.0-beta.3",
            "cli__os": "darwin",
            "cli__arch": "arm64",
            "organisation__id": organisation.pk,
            "status": "success",
            "amplitude__user_id": str(staff_user.uuid),
        }
    ]


def test_cli_usage_logger_middleware__unauthenticated_cli_request__logs_nothing(
    api_client: APIClient,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    response = api_client.get(
        "/api/v1/projects/",
        HTTP_USER_AGENT="flagsmith-cli/2.0.0 (linux/amd64)",
    )

    # Then
    assert response.status_code == 401
    assert log.events == []


def test_cli_usage_logger_middleware__master_api_key_request__logs_organisation_without_amplitude_user_id(
    admin_master_api_key_client: APIClient,
    organisation: Organisation,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    response = admin_master_api_key_client.get(
        "/api/v1/projects/",
        HTTP_USER_AGENT="flagsmith-cli/2.0.0 (linux/amd64)",
    )

    # Then
    assert response.status_code == 200
    assert log.events == [
        {
            "level": "info",
            "event": "request.made",
            "cli__version": "2.0.0",
            "cli__os": "linux",
            "cli__arch": "amd64",
            "organisation__id": organisation.pk,
            "status": "success",
        }
    ]


@pytest.mark.usefixtures("recording_span")
def test_cli_usage_logger_middleware__500_response__logs_error_status(
    staff_user: FFAdminUser,
    organisation: Organisation,
    log: StructuredLogCapture,
) -> None:
    # Given
    set_span_attribute("organisation.id", organisation.pk)

    request = HttpRequest()
    request.user = staff_user
    request.META["HTTP_USER_AGENT"] = "flagsmith-cli/2.0.0 (linux/amd64)"

    middleware = CLIUsageLoggerMiddleware(lambda request: HttpResponse(status=500))

    # When
    response = middleware(request)

    # Then
    assert response.status_code == 500
    assert log.events == [
        {
            "level": "info",
            "event": "request.made",
            "cli__version": "2.0.0",
            "cli__os": "linux",
            "cli__arch": "amd64",
            "organisation__id": organisation.pk,
            "status": "error",
            "amplitude__user_id": str(staff_user.uuid),
        }
    ]


@pytest.mark.usefixtures("recording_span")
def test_cli_usage_logger_middleware__version_with_spaces__preserves_version_unchanged(
    staff_user: FFAdminUser,
    organisation: Organisation,
    log: StructuredLogCapture,
) -> None:
    # Given
    set_span_attribute("organisation.id", organisation.pk)

    request = HttpRequest()
    request.user = staff_user
    request.META["HTTP_USER_AGENT"] = "flagsmith-cli/dev (abcdefg) (linux/amd64)"

    middleware = CLIUsageLoggerMiddleware(lambda request: HttpResponse(status=200))

    # When
    response = middleware(request)

    # Then
    assert response.status_code == 200
    assert log.events == [
        {
            "level": "info",
            "event": "request.made",
            "cli__version": "dev (abcdefg)",
            "cli__os": "linux",
            "cli__arch": "amd64",
            "organisation__id": organisation.pk,
            "status": "success",
            "amplitude__user_id": str(staff_user.uuid),
        }
    ]


def test_cli_usage_logger_middleware__non_cli_user_agent__logs_nothing(
    staff_user: FFAdminUser,
    log: StructuredLogCapture,
) -> None:
    # Given
    request = HttpRequest()
    request.user = staff_user
    request.META["HTTP_USER_AGENT"] = "Mozilla/5.0"

    middleware = CLIUsageLoggerMiddleware(lambda request: HttpResponse(status=200))

    # When
    response = middleware(request)

    # Then
    assert response.status_code == 200
    assert log.events == []


def test_cli_usage_logger_middleware__master_api_key__makes_no_database_queries(
    api_key_user: APIKeyUser,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    # Given
    request = HttpRequest()
    setattr(request, "user", api_key_user)
    request.META["HTTP_USER_AGENT"] = "flagsmith-cli/2.0.0 (linux/amd64)"

    middleware = CLIUsageLoggerMiddleware(lambda request: HttpResponse(status=200))

    # When / Then
    with django_assert_num_queries(0):
        response = middleware(request)

    assert response.status_code == 200
