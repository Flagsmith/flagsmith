from django.apps import AppConfig


class OAuth2MetadataConfig(AppConfig):
    name = "oauth2_metadata"

    def ready(self) -> None:
        from oauth2_metadata import tasks  # noqa: F401
