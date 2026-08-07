from django.http import QueryDict


class NullCharacterQueryParamMiddleware:
    """
    Strip NUL (0x00) characters from query parameter values.

    Prevents ValueError exceptions when query parameter values containing
    null characters are passed to database queries.
    """

    def __init__(self, get_response):  # type: ignore[no-untyped-def]
        self.get_response = get_response

    def __call__(self, request):  # type: ignore[no-untyped-def]
        if "\x00" in request.META.get("QUERY_STRING", ""):
            sanitized = QueryDict(mutable=True)
            for key, values in request.GET.lists():
                sanitized_key = key.replace("\x00", "")
                sanitized.setlist(
                    sanitized_key,
                    [v.replace("\x00", "") for v in values],
                )
            request.GET = sanitized
            request.META["QUERY_STRING"] = request.META["QUERY_STRING"].replace(
                "\x00", ""
            )

        return self.get_response(request)
