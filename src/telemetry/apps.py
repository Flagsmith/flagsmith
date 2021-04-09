from django.apps import AppConfig
from django.conf import settings


class TelemetryConfig(AppConfig):
    name = "telemetry"

    def ready(self):
        # Check that the app has a database connection configured so that it doesn't
        # fail when running e.g. collectstatic
        if settings.ENABLE_TELEMETRY and getattr(settings, "DATABASES", None):
            from .telemetry import SelfHostedTelemetryWrapper

            telemetry = SelfHostedTelemetryWrapper()
            telemetry.send_heartbeat()
