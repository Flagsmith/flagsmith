import logging

from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class TelemetryConfig(AppConfig):
    name = "telemetry"

    def ready(self):
        if settings.ENABLE_TELEMETRY:
            try:
                from .telemetry import SelfHostedTelemetryWrapper

                telemetry = SelfHostedTelemetryWrapper()
                telemetry.send_heartbeat()
            except Exception as e:
                logger.debug(
                    "Failed to send Telemetry data to Flagsmith. Exception was %s" % e
                )
