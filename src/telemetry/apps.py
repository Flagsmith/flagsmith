from django.apps import AppConfig
from django.conf import settings


class TelemetryConfig(AppConfig):
    name = "telemetry"

    def ready(self):
        if settings.ENABLE_TELEMETRY:
            from .telemetry import SelfHostedTelemetryWrapper

            telemetry = SelfHostedTelemetryWrapper()
            telemetry.send_heartbeat()
