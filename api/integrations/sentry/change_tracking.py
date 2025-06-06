import json
import logging
from typing import Any

import requests
from django.core.serializers.json import DjangoJSONEncoder

from core.signing import sign_payload
from features.models import FeatureState

from .models import SentryChangeTrackingConfiguration

logger = logging.getLogger(__name__)


def post_change_tracking_update_to_sentry(
    feature_state: FeatureState,
    configuration: SentryChangeTrackingConfiguration,
) -> None:
    """
    Send a Change Tracking update to Sentry

    Spec: https://github.com/getsentry/sentry/blob/master/src/sentry/flags/docs/api.md#create-generic-flag-log-post

    NOTE:
    - This works when creating the flag because there is a hook to create (save) a feature state.
    - This works when updating the flag because there is a signal to trigger this on model save.
    - This works when deleting the flag because deleting means saving the model instance with a deleted_at timestamp.
    """
    feature_name = feature_state.feature.name
    logger.debug("Sending '%s' update to Sentry...", feature_name)

    # Sentry-specific fields
    sentry_payload: dict[str, Any] = {
        "created_at": (  # i.e. Sentry event's created_at
            feature_state.deleted_at
            or feature_state.live_from
            or feature_state.updated_at
        ).isoformat(timespec="seconds"),
        "flag": feature_state.feature.name,
    }
    sentry_payload["created_by"] = {
        "id": _guess_change_author_email(feature_state),
        "type": "email",
    }
    sentry_payload["action"] = action = _guess_action(feature_state)
    if action == "updated":
        sentry_payload["change_id"] = str(feature_state.pk)

    payload = {
        "data": [sentry_payload],
        "meta": {"version": 1},
    }
    json_payload = json.dumps(payload, sort_keys=True, cls=DjangoJSONEncoder)

    headers = {
        "Content-Type": "application/json",
        "X-Sentry-Signature": sign_payload(json_payload, configuration.secret),
    }

    response = requests.post(
        url=configuration.webhook_url,
        headers=headers,
        data=json_payload,
    )

    try:
        response.raise_for_status()
    except requests.exceptions.RequestException as error:
        logger.error("Failed to send Sentry update: %s", repr(error))
        # TODO: Should we retry, or ultimately notify the admin of a persisting issue?

    logger.info("Sent '%s' (%s) to Sentry", feature_name, action)


def _guess_action(feature_state: FeatureState) -> str:
    """
    Detect which kind of event occurred for a feature state
    """
    if feature_state.deleted_at:
        return "deleted"

    # NOTE: 0~1 items depending on whether this runs synchronously
    is_new_feature = feature_state.history.order_by()[:2].count() <= 1
    if is_new_feature:
        return "created"

    return "updated"


def _guess_change_author_email(feature_state: FeatureState) -> str:
    """
    Best-effort to find the author of a feature state change

    NOTE: Audit logs are created asynchronously to this function, meaning that
    we cannot expect the most recent audit log to be what we're looking for.

    TODO: Revisit this if the actor is a relevant piece of information.
    """
    return "app@flagsmith.com"  # :(
