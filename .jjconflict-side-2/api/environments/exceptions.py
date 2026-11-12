from rest_framework.exceptions import NotFound


class EnvironmentHeaderNotPresentError(Exception):
    pass


class EnvironmentNotFoundError(NotFound):
    """Raised where an environment key does not exist, or is hidden from the caller."""

    default_code = "environment_not_found"

    def __init__(self, environment_api_key: str) -> None:
        super().__init__(
            {
                "code": self.default_code,
                "message": f"Environment key '{environment_api_key}' does not exist.",
            }
        )
