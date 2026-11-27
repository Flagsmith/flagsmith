import logging
from typing import Any

import requests
import structlog

from audit.models import AuditLog
from integrations.common.wrapper import AbstractBaseEventIntegrationWrapper

logger = logging.getLogger(__name__)
structlog_logger = structlog.get_logger("discord")

# Discord limits: embed title 256 characters, description 4096.
EMBED_TITLE_LIMIT = 256
EMBED_DESCRIPTION_LIMIT = 4096
FLAGSMITH_PURPLE = 0x6837FC


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


class DiscordWrapper(AbstractBaseEventIntegrationWrapper):
    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    @staticmethod
    def generate_event_data(audit_log_record: AuditLog) -> dict[str, Any]:
        details = (
            [f"**Project:** {audit_log_record.project.name}"]
            if audit_log_record.project
            else []
        )
        if audit_log_record.environment:  # environment_name falls back to "unknown"
            details.append(f"**Environment:** {audit_log_record.environment.name}")
        details.append(f"**By:** {audit_log_record.author_identifier}")
        return {
            "username": "Flagsmith",
            "embeds": [
                {
                    "title": _clip(audit_log_record.log, EMBED_TITLE_LIMIT),
                    "description": _clip("\n".join(details), EMBED_DESCRIPTION_LIMIT),
                    "color": FLAGSMITH_PURPLE,
                    "timestamp": audit_log_record.created_date.isoformat(),
                }
            ],
            # Never ping anyone, even if a flag or segment name contains @everyone.
            "allowed_mentions": {"parse": []},
        }

    def _track_event(self, event: dict[str, Any]) -> None:
        response = requests.post(self.webhook_url, json=event, timeout=10)
        if not response.ok:
            # 404: the webhook was deleted in Discord; 429: rate limited.
            structlog_logger.warning(
                "webhook.failed",
                response__status_code=response.status_code,
            )
            return
        logger.debug(
            "Sent event to Discord. Response code was %s", response.status_code
        )
