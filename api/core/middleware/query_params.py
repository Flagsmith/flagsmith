from collections.abc import Callable

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest


class RejectNulByteQueryParamsMiddleware:
    """
    Reject requests whose query parameters contain a NUL (0x00) character.

    Passing one through to a query against the string field of a Postgres
    row raises an unhandled `ValueError: A string literal cannot contain
    NUL (0x00) characters`, so reject it here, before any view can pass it
    to the ORM.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # `.values()` only yields the last value per key: a repeated key
        # (`?a=x&a=y`) would let a NUL byte in an earlier value slip through.
        # `.lists()` yields every value for every key.
        if any(
            "\x00" in value for _, values in request.GET.lists() for value in values
        ):
            return HttpResponseBadRequest(
                "Query parameters must not contain NUL characters."
            )
        return self.get_response(request)
