from rest_framework.views import exception_handler


class ImproperlyConfiguredError(RuntimeError):
    pass


def custom_api_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if response is not None and hasattr(exc, "get_codes"):
        if isinstance(response.data, dict) and "detail" in response.data:
            codes = exc.get_codes()
            if isinstance(codes, str):
                response.data["code"] = codes

    return response
