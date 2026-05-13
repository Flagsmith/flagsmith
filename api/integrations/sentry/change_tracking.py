import json
from datetime import datetime
from typing import Any

import requests
import structlog
from django.core.serializers.json import DjangoJSONEncoder

from core.signing import sign_payload
from features.models import FeatureState
from integrations.common.wrapper import AbstractBaseEventIntegrationWrapper
from util.util import postpone

logger = structlog.get_logger("sentry_change_tracking")

_DEFAULT_AUTHOR_EMAIL = "app@flagsmith.com"


class SentryChangeTracking(AbstractBaseEventIntegrationWrapper):
    """
    Change Tracking integration with Sentry

    Spec: https://github.com/getsentry/sentry/blob/master/src/sentry/flags/docs/api.md#create-generic-flag-log-post

    NOTE: This triggers when...
    - ...creating the flag because there is a hook to create (save) the initial feature state.
    - ...updating the flag because there is a signal to trigger this on model save.
    - ...deleting the flag because deleting means saving the model instance with a deleted_at timestamp.
    """

    def __init__(self, webhook_url: str, secret: str) -> None:
        self.webhook_url = webhook_url
        self.secret = secret

    @staticmethod
    def build_payload_entry(
        *,
        action: str,
        flag_name: str,
        change_id: Any,
        timestamp: datetime,
        author_email: str,
    ) -> dict[str, Any]:
        """Shared shape for a single `data[]` entry in a Sentry flag-log payload."""
        return {
            "action": action,
            "flag": flag_name,
            "created_at": timestamp.isoformat(timespec="seconds"),
            "created_by": {"id": author_email, "type": "email"},
            "change_id": str(change_id),
        }

    @staticmethod
    def generate_event_data(feature_state: FeatureState) -> dict[str, Any]:
        timestamp = feature_state.deleted_at or (
            max(feature_state.live_from, feature_state.updated_at)
            if feature_state.live_from
            else feature_state.updated_at
        )

        history_record = feature_state.history.first()
        if history_record is None:  # pragma: no cover
            return {}

        action = {
            "+": "created",
            "-": "deleted",
            "~": "updated",
        }[history_record.history_type]

        return SentryChangeTracking.build_payload_entry(
            action=action,
            flag_name=feature_state.feature.name,
            change_id=feature_state.pk,
            timestamp=timestamp,
            author_email=getattr(
                history_record.history_user, "email", _DEFAULT_AUTHOR_EMAIL
            ),
        )

    def _track_event(self, event: dict[str, Any]) -> None:
        self._send_events([event])

    @postpone  # type: ignore[misc]
    def track_events_async(self, events: list[dict[str, Any]]) -> None:
        self._send_events(events)

    def _send_events(self, events: list[dict[str, Any]]) -> None:
        if not events:
            return

        # All entries in a batched payload share the same flag (one EFV = one feature).
        first_event = events[0]
        action = first_event["action"]
        feature_name = first_event["flag"]

        log = logger.bind(
            sentry_action=action,
            feature_name=feature_name,
        )

        payload = {
            "data": events,
            "meta": {"version": 1},
        }
        json_payload = json.dumps(payload, sort_keys=True, cls=DjangoJSONEncoder)

        headers = {
            "Content-Type": "application/json",
            "X-Sentry-Signature": sign_payload(json_payload, self.secret),
        }

        log.debug(
            "sending",
            url=self.webhook_url,
            headers=headers,
            payload=payload,
        )

        try:
            response = requests.post(
                url=self.webhook_url,
                headers=headers,
                data=json_payload,
            )
            response.raise_for_status()  # NOTE: This is for future-proofing, as Sentry won't respond 4xx.
        except requests.exceptions.RequestException as error:
            log.warning(
                "request-failure",
                error=error,
            )
            return

        if not response.text:  # This is fragile and undocumented. ¯\_(ツ)_/¯
            log.info("success")
            return

        log.warning(
            "integration-error",
            sentry_response_status=response.status_code,
            sentry_response_body=response.text,
        )
