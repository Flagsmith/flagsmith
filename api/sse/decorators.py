def generate_identity_update_message(
    get_data_from_req=lambda req: (
        req.environment.api_key,
        req.data["identity"].get("identifier"),
    )
):
    def decorator(func):
        def wraps(*args, **kwargs):
            request = args[1]
            result = func(*args, **kwargs)
            if result.status_code < 299:
                api_key, identifier = get_data_from_req(request)
                # TODO: send identity update message
            return result

        return wraps

    return decorator
