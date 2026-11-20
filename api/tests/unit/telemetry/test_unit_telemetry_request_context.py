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
from organisations.models import Organisation
from telemetry.request_context import bind_api_request_context
from users.models import FFAdminUser

REQUEST_CONTEXT_NAMES = ("organisation__id", "project__id", "user__id")


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


def test_api_view__ffadmin_user_on_project_route__binds_user_and_project(
    api_request_factory: APIRequestFactory,
    staff_user: FFAdminUser,
) -> None:
    # Given
    request = api_request_factory.get("/")
    force_authenticate(request, user=staff_user)

    # When
    response = RequestContextView.as_view()(request, project_pk="42")

    # Then
    assert response.data == {
        "organisation__id": None,  # Left to the permission layer
        "project__id": 42,
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


@pytest.mark.parametrize(
    "project_pk, expected_project_id",
    [
        (42, 42),
        ("42", 42),
        ("not-a-project", None),
        (None, None),
    ],
)
def test_bind_api_request_context__project_pk_kwarg__binds_numeric_project_id(
    api_request_factory: APIRequestFactory,
    project_pk: typing.Any,
    expected_project_id: int | None,
) -> None:
    # Given
    request = Request(api_request_factory.get("/"))
    view = APIView()
    view.kwargs = {"project_pk": project_pk}

    # When
    bind_api_request_context(request, view)

    # Then
    assert get_request_context("project__id") == expected_project_id
