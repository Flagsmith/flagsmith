import logging

from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate

logger = logging.getLogger(__name__)


def send_telemetry_callback(sender, **kwargs):
    if settings.ENABLE_TELEMETRY:
        try:
            from .telemetry import SelfHostedTelemetryWrapper

            telemetry = SelfHostedTelemetryWrapper()
            telemetry.send_heartbeat()
        except Exception as e:
            logger.debug(
                "Failed to send Telemetry data to Flagsmith. Exception was %s" % e
            )
    pass


class TelemetryConfig(AppConfig):
    name = "telemetry"

    def ready(self):
        post_migrate.connect(send_telemetry_callback, sender=self)
