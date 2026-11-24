import typing
from collections.abc import Generator

import pytest
import structlog.contextvars
from common.core.request_context import get_request_context
from django.contrib.auth.models import AnonymousUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

from api_keys.authentication import MasterAPIKeyAuthentication
from api_keys.models import MasterAPIKey
from environments.models import Environment
from features.models import Feature
from organisations.models import Organisation
from projects.models import Project
from telemetry.request_context import bind_api_request_context
from users.models import FFAdminUser

REQUEST_CONTEXT_NAMES = (
    "environment__id",
    "feature__id",
    "organisation__id",
    "project__id",
    "user__id",
)


class RequestContextView(APIView):
    """Respond with the request context bound by the time the view handles it"""

    authentication_classes = [MasterAPIKeyAuthentication]
    permission_classes: list[type] = []

    def get(self, request: Request, **kwargs: typing.Any) -> Response:
        return Response(
            {name: get_request_context(name) for name in REQUEST_CONTEXT_NAMES}
        )


@pytest.fixture(autouse=True)
def clear_request_context() -> Generator[None, None, None]:
    # Bypassing `RequestContextMiddleware`, bindings would outlive the test
    yield
    structlog.contextvars.clear_contextvars()


@pytest.fixture()
def api_request_factory() -> APIRequestFactory:
    return APIRequestFactory()


def _bind(
    api_request_factory: APIRequestFactory,
    **url_kwargs: typing.Any,
) -> dict[str, typing.Any]:
    request = Request(api_request_factory.get("/"))
    view = APIView()
    view.kwargs = url_kwargs
    bind_api_request_context(request, view)
    return {name: get_request_context(name) for name in REQUEST_CONTEXT_NAMES}


def test_api_view__ffadmin_user__binds_user(
    api_request_factory: APIRequestFactory,
    staff_user: FFAdminUser,
) -> None:
    # Given
    request = api_request_factory.get("/")
    force_authenticate(request, user=staff_user)

    # When
    response = RequestContextView.as_view()(request)

    # Then
    assert response.data == {
        "environment__id": None,
        "feature__id": None,
        "organisation__id": None,
        "project__id": None,
        "user__id": str(staff_user.uuid),
    }


def test_api_view__master_api_key__binds_key_organisation_only(
    api_request_factory: APIRequestFactory,
    admin_master_api_key: tuple[MasterAPIKey, str],
    organisation: Organisation,
) -> None:
    # Given
    _, key = admin_master_api_key
    request = api_request_factory.get("/", HTTP_AUTHORIZATION=f"Api-Key {key}")

    # When
    response = RequestContextView.as_view()(request)

    # Then
    assert response.data == {
        "environment__id": None,
        "feature__id": None,
        "organisation__id": organisation.id,
        "project__id": None,
        "user__id": None,
    }


@pytest.mark.parametrize("user", [None, AnonymousUser()])
def test_api_view__no_user__binds_nothing(
    api_request_factory: APIRequestFactory,
    user: AnonymousUser | None,
) -> None:
    # Given
    # e.g. `EnvironmentKeyAuthentication` authenticates SDK requests as `None`
    request = api_request_factory.get("/")
    force_authenticate(request, user=user)

    # When
    response = RequestContextView.as_view()(request)

    # Then
    assert response.data == {name: None for name in REQUEST_CONTEXT_NAMES}


def test_api_view__project_and_feature_route__binds_url_entities(
    api_request_factory: APIRequestFactory,
    staff_user: FFAdminUser,
    project: Project,
    feature: Feature,
) -> None:
    # Given
    request = api_request_factory.get("/")
    force_authenticate(request, user=staff_user)

    # When
    response = RequestContextView.as_view()(
        request,
        project_pk=str(project.id),
        feature_pk=str(feature.id),
    )

    # Then
    assert response.data == {
        "environment__id": None,
        "feature__id": feature.id,
        "organisation__id": project.organisation_id,
        "project__id": project.id,
        "user__id": str(staff_user.uuid),
    }


# Routers capture strings, path converters ints
@pytest.mark.parametrize("to_url_kwarg", [str, int])
def test_bind_api_request_context__project_pk__binds_project_and_organisation(
    api_request_factory: APIRequestFactory,
    project: Project,
    to_url_kwarg: typing.Callable[[int], str | int],
    django_assert_num_queries: typing.Any,
) -> None:
    # Given / When
    with django_assert_num_queries(1):
        bound = _bind(api_request_factory, project_pk=to_url_kwarg(project.id))

    # Then
    assert bound["project__id"] == project.id
    assert bound["organisation__id"] == project.organisation_id


def test_bind_api_request_context__deleted_project__binds_project_only(
    api_request_factory: APIRequestFactory,
    project: Project,
) -> None:
    # Given
    project.delete()

    # When
    bound = _bind(api_request_factory, project_pk=str(project.id))

    # Then
    assert bound["project__id"] == project.id
    assert bound["organisation__id"] is None


def test_bind_api_request_context__environment_api_key__binds_environment_project_and_organisation(
    api_request_factory: APIRequestFactory,
    environment: Environment,
    django_assert_num_queries: typing.Any,
) -> None:
    # Given / When
    with django_assert_num_queries(1):
        bound = _bind(api_request_factory, environment_api_key=environment.api_key)

    # Then
    assert bound == {
        "environment__id": environment.id,
        "feature__id": None,
        "organisation__id": environment.project.organisation_id,
        "project__id": environment.project_id,
        "user__id": None,
    }


def test_bind_api_request_context__unknown_environment_api_key__binds_nothing(
    api_request_factory: APIRequestFactory,
    db: None,
) -> None:
    # Given / When
    bound = _bind(api_request_factory, environment_api_key="unknown")

    # Then
    assert bound == {name: None for name in REQUEST_CONTEXT_NAMES}


@pytest.mark.parametrize("value", ["not-an-id", None])
def test_bind_api_request_context__non_numeric_ids__binds_nothing(
    api_request_factory: APIRequestFactory,
    db: None,
    value: str | None,
    django_assert_num_queries: typing.Any,
) -> None:
    # Given / When
    with django_assert_num_queries(0):
        bound = _bind(api_request_factory, project_pk=value, feature_pk=value)

    # Then
    assert bound == {name: None for name in REQUEST_CONTEXT_NAMES}
