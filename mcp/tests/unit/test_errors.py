import httpx
import pytest

from flagsmith_mcp.errors import upstream_status_code


@pytest.fixture
def http_status_error() -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "https://api.flagsmith.com/api/v1/organisations/")
    return httpx.HTTPStatusError(
        "Client error '401 Unauthorized'",
        request=request,
        response=httpx.Response(401, request=request),
    )


def test_upstream_status_code__no_exception__returns_none() -> None:
    # Given no exception at all
    # When / Then
    assert upstream_status_code(None) is None


def test_upstream_status_code__unrelated_exception__returns_none() -> None:
    # Given an error with no upstream response behind it
    exc = ValueError("something else went wrong")

    # When / Then
    assert upstream_status_code(exc) is None


def test_upstream_status_code__status_error_itself__returns_status(
    http_status_error: httpx.HTTPStatusError,
) -> None:
    # Given a rejected upstream response, unwrapped
    # When / Then
    assert upstream_status_code(http_status_error) == 401


def test_upstream_status_code__explicit_cause__returns_status(
    http_status_error: httpx.HTTPStatusError,
) -> None:
    # Given the `raise ... from e` chain FastMCP's OpenAPI provider builds
    exc = ValueError("HTTP error 401: Unauthorized")
    exc.__cause__ = http_status_error

    # When / Then
    assert upstream_status_code(exc) == 401


def test_upstream_status_code__implicit_context__returns_status(
    http_status_error: httpx.HTTPStatusError,
) -> None:
    # Given a bare `raise` inside an `except` block, which sets __context__
    exc = ValueError("HTTP error 401: Unauthorized")
    exc.__context__ = http_status_error

    # When / Then
    assert upstream_status_code(exc) == 401


def test_upstream_status_code__nested_chain__returns_status(
    http_status_error: httpx.HTTPStatusError,
) -> None:
    # Given the full chain a failing tool call produces:
    # ToolError -> ValueError -> HTTPStatusError
    value_error = ValueError("HTTP error 401: Unauthorized")
    value_error.__cause__ = http_status_error
    tool_error = RuntimeError("Error calling tool 'list_organizations'")
    tool_error.__cause__ = value_error

    # When / Then
    assert upstream_status_code(tool_error) == 401


def test_upstream_status_code__cyclic_chain__terminates() -> None:
    # Given a chain that loops back on itself
    first = ValueError("first")
    second = ValueError("second")
    first.__context__ = second
    second.__context__ = first

    # When / Then the walk terminates rather than spinning
    assert upstream_status_code(first) is None
