from django.apps import AppConfig


class EdgeAPIIdentitiesAppConfig(AppConfig):
    name = "edge_api.identities"
    label = "edge_api_identities"

    def ready(self) -> None:
        # Import openapi extensions to register them with drf-spectacular
        from edge_api.identities import openapi  # noqa: F401
