from app.utils import create_hash

SERVER_API_KEY_PREFIX = "ser."


def generate_client_api_key():  # type: ignore[no-untyped-def]
    return generate_api_key()


def generate_server_api_key():  # type: ignore[no-untyped-def]
    return generate_api_key(prefix=SERVER_API_KEY_PREFIX)


def generate_api_key(prefix: str = ""):  # type: ignore[no-untyped-def]
    """
    Generate an API key that is unique across both Environment.api_key and
    EnvironmentAPIKey.key
    """
    return f"{prefix}{create_hash()}"
