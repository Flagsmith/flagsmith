from collections.abc import Generator

import pytest
from opentelemetry import baggage
from opentelemetry import context as otel_context
from pytest_structlog import StructuredLogCapture
from rest_framework.test import APIClient

from environments.models import Environment
from features.models import Feature, FeatureState
from organisations.models import Organisation, OrganisationRole
from projects.models import Project
from users.models import FFAdminUser


@pytest.fixture()
def mcp_baggage() -> Generator[None, None, None]:
    ctx = baggage.set_baggage("flagsmith.client.name", "flagsmith-mcp")
    token = otel_context.attach(ctx)
    yield
    otel_context.detach(token)


def test_mcp_usage_logger_middleware__no_mcp_baggage__logs_nothing(
    admin_client_new: APIClient,
    project: Project,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    admin_client_new.get(f"/api/v1/projects/{project.pk}/")

    # Then
    assert log.events == []


@pytest.mark.parametrize(
    "path_template",
    [
        # Organisation is obtained using `organisation_pk`
        "/api/v1/organisations/{organisation_pk}/invites/",
        # Organisation is obtained using `pk`
        "/api/v1/organisations/{organisation_pk}/projects/",
        # Organisation is obtained using `pk`
        "/api/v1/projects/{project_pk}/",
        "/api/v1/projects/{project_pk}/environments/",
        # Organisation is obtained using `project_pk`
        "/api/v1/projects/{project_pk}/features/",
        # Organisation is obtained using `environment_pk`
        "/api/v1/environments/{environment_pk}/features/{feature_pk}/versions/",
        # Organisation is obtained using `environment_api_key`
        "/api/v1/environments/{environment_api_key}/featurestates/{feature_state_pk}/",
    ],
)
@pytest.mark.usefixtures("mcp_baggage")
def test_mcp_usage_logger_middleware__resolvable_url__logs_expected(
    admin_client_new: APIClient,
    log: StructuredLogCapture,
    organisation: Organisation,
    project: Project,
    environment: Environment,
    feature: Feature,
    feature_state: FeatureState,
    path_template: str,
) -> None:
    # Given / When
    response = admin_client_new.get(
        path_template.format(
            organisation_pk=organisation.pk,
            project_pk=project.pk,
            environment_pk=environment.pk,
            environment_api_key=environment.api_key,
            feature_pk=feature.pk,
            feature_state_pk=feature_state.pk,
        )
    )

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
def test_mcp_usage_logger_middleware__feature_state_url__logs_expected(
    admin_client_new: APIClient,
    log: StructuredLogCapture,
    organisation: Organisation,
    feature_state: FeatureState,
) -> None:
    """Organisation is obtained using `pk` from /api/v1/features/featurestates/{pk}/."""
    # Given / When
    response = admin_client_new.get(
        f"/api/v1/features/featurestates/{feature_state.pk}/"
    )

    # Then
    assert response.status_code == 405
    assert log.events == [
        {
            "level": "info",
            "event": "tool.called",
            "organisation__id": organisation.pk,
            "status": "error",
        }
    ]


@pytest.mark.usefixtures("mcp_baggage")
def test_mcp_usage_logger_middleware__user_with_single_organisation__logs_expected(
    staff_client: APIClient,
    log: StructuredLogCapture,
    organisation: Organisation,
) -> None:
    """Organisation is obtained from the user when /api/v1/projects/ has no usable parameter."""
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


@pytest.mark.usefixtures("mcp_baggage", "organisation")
def test_mcp_usage_logger_middleware__user_with_multiple_organisations__logs_warning(
    staff_client: APIClient,
    log: StructuredLogCapture,
    staff_user: FFAdminUser,
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


@pytest.mark.usefixtures("mcp_baggage", "organisation")
def test_mcp_usage_logger_middleware__user_with_multiple_organisations__logs_url_organisation(
    staff_client: APIClient,
    log: StructuredLogCapture,
    staff_user: FFAdminUser,
) -> None:
    # Given
    other_organisation = Organisation.objects.create(name="Other Org")
    staff_user.add_organisation(other_organisation, role=OrganisationRole.USER)

    # When
    response = staff_client.get(
        f"/api/v1/organisations/{other_organisation.pk}/projects/"
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


@pytest.mark.usefixtures("mcp_baggage", "organisation")
def test_mcp_usage_logger_middleware__user_not_in_url_organisation__logs_warning(
    staff_client: APIClient,
    log: StructuredLogCapture,
    staff_user: FFAdminUser,
) -> None:
    # Given
    other_organisation = Organisation.objects.create(name="Other Org")
    foreign_organisation = Organisation.objects.create(name="Foreign Org")
    staff_user.add_organisation(other_organisation, role=OrganisationRole.USER)

    # When
    response = staff_client.get(
        f"/api/v1/organisations/{foreign_organisation.pk}/projects/"
    )

    # Then
    assert response.status_code == 404
    assert log.events == [
        {
            "level": "warning",
            "event": "tool.called",
            "organisation__id": None,
            "status": "error",
        }
    ]


@pytest.mark.usefixtures("mcp_baggage", "organisation")
def test_mcp_usage_logger_middleware__user_not_in_url_param_organisation__logs_warning(
    staff_client: APIClient,
    log: StructuredLogCapture,
    staff_user: FFAdminUser,
) -> None:
    # Given
    other_organisation = Organisation.objects.create(name="Other Org")
    foreign_organisation = Organisation.objects.create(name="Foreign Org")
    staff_user.add_organisation(other_organisation, role=OrganisationRole.USER)

    # When
    response = staff_client.get(
        f"/api/v1/organisations/{foreign_organisation.pk}/invites/"
    )

    # Then
    assert response.status_code == 403
    assert log.events == [
        {
            "level": "warning",
            "event": "tool.called",
            "organisation__id": None,
            "status": "error",
        }
    ]


@pytest.mark.usefixtures("mcp_baggage")
def test_mcp_usage_logger_middleware__unauthenticated__logs_nothing(
    api_client: APIClient,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    response = api_client.get("/api/v1/projects/")

    # Then
    assert response.status_code == 401
    assert log.events == []
