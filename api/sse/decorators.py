import typing

from .exceptions import ViewResponseDoesNotHaveStatus
from .sse_service import send_identity_update_message


def generate_identity_update_message(
    get_data_from_req_callable=lambda req: (
        req.environment,
        req.data["identity"].get("identifier"),
    )
):
    """
    Wraps a view method that sends an identity update message if the view returns a 2XX response

    Args:
        get_data_from_req_callable (Callable): A callable that takes a request object and returns a tuple of
            (environment, identifier)

    """

    def decorator(view_func: typing.Callable, *args, **kwargs):
        def view_wrapper(*args, **kwargs):
            request = args[0]
            result = view_func(*args, **kwargs)
            if not hasattr(result, "status_code"):
                raise ViewResponseDoesNotHaveStatus()

            if result.status_code < 299:
                environment, identifier = get_data_from_req_callable(request)
                if environment.project.organisation.persist_trait_data:
                    send_identity_update_message(environment, identifier)
            return result

        return view_wrapper

    return decorator
