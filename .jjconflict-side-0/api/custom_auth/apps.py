from django.apps import AppConfig


class CustomAuthAppConfig(AppConfig):
    name = "custom_auth"

    def ready(self) -> None:
        from custom_auth import signals  # noqa F401
        from custom_auth.jwt_cookie import signals as jwt_cookie_signals  # noqa F401
