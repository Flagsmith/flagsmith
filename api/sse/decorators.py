import typing

from .tasks import send_identity_update_message


def generate_identity_update_message(
    get_data_from_req_callable=lambda req: (
        req.environment,
        req.data["identity"].get("identifier"),
    )
):
    """
    Warps a view method that send an identity update message if the view returns a 2XX response

    Args:
        get_data_from_req_callable (Callable): A callable that takes a request object and returns a tuple of
            (environment, identifier)

    Usage:
    @method_decorator(
        generate_identity_update_message(
            lambda req: (req.environment, req.data["identifier"])
        )
    )
    def post(self, request, *args, **kwargs):


    """

    def decorator(view_func: typing.Callable, *args, **kwargs):
        def view_wrapper(*args, **kwargs):
            request = args[0]
            result = view_func(*args, **kwargs)
            if result.status_code < 299:
                environment, identifier = get_data_from_req_callable(request)
                if environment.project.organisation.persist_trait_data:
                    send_identity_update_message.delay(
                        args=(environment.api_key, identifier)
                    )
            return result

        return view_wrapper

    return decorator
