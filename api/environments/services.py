from environments.exceptions import EnvironmentNotFoundError
from environments.models import Environment


def get_environment(environment_api_key: str) -> Environment:
    """Fetch an environment by its client-side key, or refuse with a 404."""
    try:
        return Environment.objects.get(api_key=environment_api_key)  # type: ignore[no-any-return]
    except Environment.DoesNotExist:
        raise EnvironmentNotFoundError(environment_api_key) from None
