from django.apps import AppConfig


class IdentitiesConfig(AppConfig):
    name = "environments.identities"

    def ready(self) -> None:
        # Import openapi extensions to register them with drf-spectacular
        from environments.identities.traits import openapi  # noqa: F401
