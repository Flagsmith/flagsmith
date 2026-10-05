import json
from typing import Any

import structlog
from django.conf import settings
from django.dispatch import receiver
from djoser.signals import user_activated  # type: ignore[import-untyped]
from openfeature.evaluation_context import EvaluationContext

from integrations.flagsmith.client import get_openfeature_client
from integrations.lead_tracking.hubspot.tasks import (
    create_hubspot_contact_for_user,
)
from users.models import FFAdminUser

logger = structlog.get_logger("signup")


@receiver(user_activated)
def create_hubspot_contact_on_activation(
    user: FFAdminUser,
    **kwargs: Any,
) -> None:
    if settings.ENABLE_HUBSPOT_LEAD_TRACKING:
        create_hubspot_contact_for_user.delay(args=(user.id,))


@receiver(user_activated)
def track_signup_conversion_on_activation(
    user: FFAdminUser,
    **kwargs: Any,
) -> None:
    try:
        onboarding = json.loads(user.onboarding_data) if user.onboarding_data else {}
        if not (signup_anonymous_id := onboarding.get("signup_anonymous_id")):
            return
        get_openfeature_client().track(
            "signup_activated",
            evaluation_context=EvaluationContext(targeting_key=signup_anonymous_id),
        )
    except Exception:
        logger.exception("conversion.tracking_failed", user__id=user.id)
