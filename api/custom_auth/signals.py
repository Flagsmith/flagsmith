from typing import Any

from django.conf import settings
from django.dispatch import receiver
from djoser.signals import user_activated  # type: ignore[import-untyped]

from integrations.lead_tracking.hubspot.tasks import (
    create_hubspot_contact_for_user,
)
from users.models import FFAdminUser


@receiver(user_activated)
def create_hubspot_contact_on_activation(
    user: FFAdminUser,
    **kwargs: Any,
) -> None:
    if settings.ENABLE_HUBSPOT_LEAD_TRACKING:
        create_hubspot_contact_for_user.delay(args=(user.id,))
