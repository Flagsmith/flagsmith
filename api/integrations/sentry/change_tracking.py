import json
import logging
from typing import Any

import requests
from django.core.serializers.json import DjangoJSONEncoder

from audit.models import AuditLog
from audit.services import get_audited_instance_from_audit_log_record
from core.signing import sign_payload
from features.models import FeatureState
from integrations.common.exceptions import InvalidIntegrationParameters
from integrations.common.wrapper import AbstractBaseEventIntegrationWrapper

logger = logging.getLogger(__name__)


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
    def generate_event_data(audit_log_record: AuditLog) -> dict[str, Any]:
        feature_state = get_audited_instance_from_audit_log_record(audit_log_record)
        if not (
            feature_state and isinstance(feature_state, FeatureState)
        ):  # pragma: no cover
            raise InvalidIntegrationParameters(
                f"{repr(feature_state)} is not a FeatureState object."
            )

        update_published_at = feature_state.deleted_at or (
            max(feature_state.live_from, feature_state.updated_at)
            if feature_state.live_from
            else feature_state.updated_at
        )

        action = {
            "+": "created",
            "-": "deleted",
            "~": "updated",
        }[audit_log_record.history_record.history_type]  # type: ignore[union-attr]

        inner_payload = {
            "action": action,
            "flag": feature_state.feature.name,
            "created_at": update_published_at.isoformat(timespec="seconds"),
            "created_by": {
                "id": getattr(audit_log_record.author, "email", "app@flagsmith.com"),
                "type": "email",
            },
        }

        if action == "updated":
            inner_payload["change_id"] = str(feature_state.pk)

        return inner_payload

    def _track_event(self, event: dict[str, Any]) -> None:
        action = event["action"]
        feature_name = event["flag"]
        logger.debug("Sending '%s' (%s) to Sentry...", feature_name, action)

        payload = {
            "data": [event],
            "meta": {"version": 1},
        }
        json_payload = json.dumps(payload, sort_keys=True, cls=DjangoJSONEncoder)

        headers = {
            "Content-Type": "application/json",
            "X-Sentry-Signature": sign_payload(json_payload, self.secret),
        }

        response = requests.post(
            url=self.webhook_url,
            headers=headers,
            data=json_payload,
        )

        try:
            response.raise_for_status()
        except requests.exceptions.RequestException as error:
            # TODO: Should we retry, or ultimately notify the admin of a persisting issue?
            logger.error(
                "Error sending '%s' (%s) to Sentry: %s",
                feature_name,
                action,
                repr(error),
            )
        else:
            logger.debug("Sent '%s' (%s) to Sentry", feature_name, action)
