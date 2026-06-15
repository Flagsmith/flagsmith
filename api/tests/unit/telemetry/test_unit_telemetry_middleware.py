import pytest
from pytest_structlog import StructuredLogCapture
from rest_framework.test import APIClient

from environments.models import Environment
from organisations.models import Organisation, OrganisationRole
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
