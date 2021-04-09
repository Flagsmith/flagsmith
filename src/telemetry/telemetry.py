import json
import logging

import requests

from telemetry.models import TelemetryData
from telemetry.serializers import TelemetrySerializer

logger = logging.getLogger(__name__)


class SelfHostedTelemetryWrapper:
    TELEMETRY_API_URI = "https://api.flagsmith.com/api/v1/analytics/telemetry/"

    def send_heartbeat(self) -> None:
        telemetry_data = TelemetryData.generate_telemetry_data()
        serializer = TelemetrySerializer(instance=telemetry_data)
        self._send(serializer.data)

    def _send(self, data: dict) -> None:
        try:
            response = requests.post(
                self.TELEMETRY_API_URI, data=json.dumps(data), timeout=2
            )
            logger.debug(
                "Sent telemetry heartbeat to Flagsmith. Response code was %s"
                % response.status_code
            )
        except requests.ConnectionError:
            logger.debug("Unable to send telemetry heartbeat to Flagsmith.")
