import pytest
import structlog
from django.http import HttpResponse
from pytest_structlog import StructuredLogCapture
from structlog.contextvars import bind_contextvars, clear_contextvars, get_contextvars

from api_keys.user import APIKeyUser
from core.middleware.structlog_context import StructlogContextMiddleware
from users.models import FFAdminUser


@pytest.fixture(autouse=True)
def _clear_structlog_contextvars():  # type: ignore[no-untyped-def]
    """Ensure each test starts and ends with a clean structlog.contextvars state."""
    clear_contextvars()
    yield
    clear_contextvars()


def test_structlog_context__without_middleware__event_only_has_manual_kwargs(
    log: StructuredLogCapture,
) -> None:
    """
    BEFORE snapshot for Flagsmith #7298.

    Demonstrates current behaviour: a logger.info call only emits the
    kwargs the caller passes explicitly. No automatic user/org/project/
    environment context is added — because no middleware binds anything
    onto structlog.contextvars yet.

    After the request-context middleware lands, a call site running inside
    a request scope would additionally pick up user.id, organisation.id,
    project.id, environment.id automatically.
    """
    # Given
    logger = structlog.get_logger("demo")

    # When — emit the kind of event that exists today at e.g.
    # api/projects/code_references/views.py:61
    logger.info(
        "scan.created",
        organisation__id=42,
        code_references__count=5,
    )

    # Then — captured event contains only what was passed in
    assert log.events == [
        {
            "level": "info",
            "event": "scan.created",
            "organisation__id": 42,
            "code_references__count": 5,
        }
    ]


def test_structlog_context__with_middleware__event_inherits_bound_contextvars(
    mocker,  # type: ignore[no-untyped-def]
    log: StructuredLogCapture,
) -> None:
    """
    AFTER snapshot for Flagsmith #7298.

    Demonstrates the behaviour with the request-context middleware in place.
    A logger.info call inside a request scope automatically picks up the
    user/org context from the middleware's contextvars bindings, even when
    the call site does NOT pass them as kwargs.

    Compare to test_structlog_context__without_middleware__event_only_has_manual_kwargs
    above (the BEFORE snapshot) — the same call site now emits an event
    carrying identifiers the caller never passed.
    """
    # Given — an authenticated FFAdminUser
    user = mocker.MagicMock(spec=FFAdminUser)
    user.is_authenticated = True
    user.uuid = "alice-uuid"
    user.organisations.first.return_value = mocker.MagicMock(id=7)
    request = mocker.MagicMock()
    request.user = user

    logger = structlog.get_logger("demo")

    def view(_request):  # type: ignore[no-untyped-def]
        # The view emits its event with ONLY the kwargs not covered by the
        # middleware. Note the absence of organisation__id — it's now bound
        # globally by the middleware and merged in automatically.

        logger.info(
            "scan.created",
            code_references__count=5,
        )
        return HttpResponse()

    middleware = StructlogContextMiddleware(view)

    # When — request flows through the middleware
    middleware(request)

    # Then — the captured event has the manual kwarg AND the auto-bound
    # user.id and organisation.id from the middleware
    assert log.events == [
        {
            "level": "info",
            "event": "scan.created",
            "user__id": "alice-uuid",
            "organisation__id": 7,
            "code_references__count": 5,
        }
    ]


def test_structlog_context_middleware__any_request__returns_response_unchanged(mocker):  # type: ignore[no-untyped-def]
    # Given
    expected_response = HttpResponse(status=200)
    middleware = StructlogContextMiddleware(lambda _request: expected_response)

    # When
    result = middleware(mocker.MagicMock())

    # Then
    assert result is expected_response


def test_structlog_context_middleware__bindings_made_in_view__cleared_after_response(
    mocker,
):  # type: ignore[no-untyped-def]
    # Given — a view that binds something onto contextvars
    def view_that_binds(_request):  # type: ignore[no-untyped-def]
        bind_contextvars(some_key="some_value")
        return HttpResponse()

    middleware = StructlogContextMiddleware(view_that_binds)

    # When
    middleware(mocker.MagicMock())

    # Then — bindings made during the request are cleared on exit
    assert get_contextvars() == {}


def test_structlog_context_middleware__view_exception__contextvars_still_cleared(
    mocker,
):  # type: ignore[no-untyped-def]
    # Given — a view that binds then raises
    def faulty_view(_request):  # type: ignore[no-untyped-def]
        bind_contextvars(some_key="some_value")
        raise ValueError("boom")

    middleware = StructlogContextMiddleware(faulty_view)

    # When / Then — exception propagates, but contextvars are still cleared
    with pytest.raises(ValueError):
        middleware(mocker.MagicMock())

    assert get_contextvars() == {}


def test_structlog_context_middleware__ffadmin_user__binds_user_id_and_organisation_id(
    mocker,
):  # type: ignore[no-untyped-def]
    # Given — an authenticated FFAdminUser with one organisation
    user = mocker.MagicMock(spec=FFAdminUser)
    user.is_authenticated = True
    user.uuid = "alice-uuid"
    user.organisations.first.return_value = mocker.MagicMock(id=42)

    captured: dict = {}

    def view_captures_context(_request):  # type: ignore[no-untyped-def]
        captured.update(get_contextvars())
        return HttpResponse()

    request = mocker.MagicMock()
    request.user = user

    middleware = StructlogContextMiddleware(view_captures_context)

    # When
    middleware(request)

    # Then — both user.id and organisation.id bound during the request
    assert captured == {"user__id": "alice-uuid", "organisation__id": 42}


def test_structlog_context_middleware__api_key_user__binds_only_organisation_id(mocker):  # type: ignore[no-untyped-def]
    # Given — an authenticated APIKeyUser (Master API Key principal).
    # APIKeyUser.key is set in __init__, so we instantiate a real one with
    # a mocked MasterAPIKey rather than spec-mocking the class (spec only
    # exposes class-level attributes).
    master_key = mocker.MagicMock()
    master_key.organisation_id = 7
    user = APIKeyUser(key=master_key)

    captured: dict = {}

    def view_captures_context(_request):  # type: ignore[no-untyped-def]
        captured.update(get_contextvars())
        return HttpResponse()

    request = mocker.MagicMock()
    request.user = user

    middleware = StructlogContextMiddleware(view_captures_context)

    # When
    middleware(request)

    # Then — only organisation.id bound. APIKeyUser has no uuid, so no
    # user.id binding (per ticket: avoids mixing identifier kinds)
    assert captured == {"organisation__id": 7}


def test_structlog_context_middleware__anonymous_user__binds_nothing(mocker):  # type: ignore[no-untyped-def]
    # Given — an unauthenticated request (e.g. DRF auth not yet resolved
    # at middleware time, or an actually-anonymous request)
    user = mocker.MagicMock()
    user.is_authenticated = False

    captured: dict = {}

    def view_captures_context(_request):  # type: ignore[no-untyped-def]
        captured.update(get_contextvars())
        return HttpResponse()

    request = mocker.MagicMock()
    request.user = user

    middleware = StructlogContextMiddleware(view_captures_context)

    # When
    middleware(request)

    # Then — nothing bound
    assert captured == {}


def test_structlog_context_middleware__ffadmin_user_with_no_organisations__binds_only_user_id(
    mocker,
):  # type: ignore[no-untyped-def]
    # Given — an FFAdminUser that belongs to no organisations
    user = mocker.MagicMock(spec=FFAdminUser)
    user.is_authenticated = True
    user.uuid = "alice-uuid"
    user.organisations.first.return_value = None

    captured: dict = {}

    def view_captures_context(_request):  # type: ignore[no-untyped-def]
        captured.update(get_contextvars())
        return HttpResponse()

    request = mocker.MagicMock()
    request.user = user

    middleware = StructlogContextMiddleware(view_captures_context)

    # When
    middleware(request)

    # Then — only user.id bound; organisation.id is skipped gracefully
    assert captured == {"user__id": "alice-uuid"}


def test_structlog_context_middleware__process_view_with_project_pk__binds_project_id(
    mocker,
):  # type: ignore[no-untyped-def]
    # Given
    middleware = StructlogContextMiddleware(lambda _r: HttpResponse())

    # When — process_view is invoked by Django with URL kwargs resolved
    middleware.process_view(
        request=mocker.MagicMock(),
        view_func=mocker.MagicMock(),
        view_args=(),
        view_kwargs={"project_pk": 42},
    )

    # Then
    assert get_contextvars() == {"project__id": 42}


def test_structlog_context_middleware__process_view_with_environment_api_key__binds_environment_id(
    mocker,
):  # type: ignore[no-untyped-def]
    # Given — Environment.get_from_cache returns a hit
    environment = mocker.MagicMock(id=99)
    mocker.patch(
        "core.middleware.structlog_context.Environment.get_from_cache",
        return_value=environment,
    )
    middleware = StructlogContextMiddleware(lambda _r: HttpResponse())

    # When
    middleware.process_view(
        request=mocker.MagicMock(),
        view_func=mocker.MagicMock(),
        view_args=(),
        view_kwargs={"environment_api_key": "some-key"},
    )

    # Then
    assert get_contextvars() == {"environment__id": 99}


def test_structlog_context_middleware__process_view_with_unknown_environment_key__binds_nothing(
    mocker,
):  # type: ignore[no-untyped-def]
    # Given — get_from_cache returns None (invalid/unknown key)
    mocker.patch(
        "core.middleware.structlog_context.Environment.get_from_cache",
        return_value=None,
    )
    middleware = StructlogContextMiddleware(lambda _r: HttpResponse())

    # When
    middleware.process_view(
        request=mocker.MagicMock(),
        view_func=mocker.MagicMock(),
        view_args=(),
        view_kwargs={"environment_api_key": "bad-key"},
    )

    # Then — no environment.id binding; lookup failure is silent
    assert get_contextvars() == {}


def test_structlog_context_middleware__process_view_without_url_kwargs__binds_nothing(
    mocker,
):  # type: ignore[no-untyped-def]
    # Given
    middleware = StructlogContextMiddleware(lambda _r: HttpResponse())

    # When — process_view called with no relevant kwargs
    middleware.process_view(
        request=mocker.MagicMock(),
        view_func=mocker.MagicMock(),
        view_args=(),
        view_kwargs={},
    )

    # Then
    assert get_contextvars() == {}


def test_structlog_context_middleware__sequential_requests_on_same_instance__no_leakage(
    mocker,
):  # type: ignore[no-untyped-def]
    """
    Cross-request leakage test (Flagsmith #7298 acceptance criterion).

    Django reuses one middleware instance per worker, and Gunicorn's gthread
    workers reuse threads across requests. Without `clear_contextvars()` in
    `finally`, request B on the same thread would inherit request A's
    bindings. This test verifies the cleanup actually works under that
    realistic reuse pattern.
    """
    # Given — a single middleware instance (the "long-lived worker")
    captured_states: list[dict] = []

    def view_captures_state(_request):  # type: ignore[no-untyped-def]
        captured_states.append(dict(get_contextvars()))
        return HttpResponse()

    middleware = StructlogContextMiddleware(view_captures_state)

    # First request: an authenticated FFAdminUser — bindings expected
    first_user = mocker.MagicMock(spec=FFAdminUser)
    first_user.is_authenticated = True
    first_user.uuid = "alice-uuid"
    first_user.organisations.first.return_value = mocker.MagicMock(id=42)
    first_request = mocker.MagicMock()
    first_request.user = first_user

    # Second request: anonymous — should see ZERO bindings
    second_user = mocker.MagicMock()
    second_user.is_authenticated = False
    second_request = mocker.MagicMock()
    second_request.user = second_user

    # When — both requests run sequentially on the same middleware
    middleware(first_request)
    middleware(second_request)

    # Then — first saw its bindings, second saw nothing leaked through
    assert captured_states[0] == {"user__id": "alice-uuid", "organisation__id": 42}
    assert captured_states[1] == {}
