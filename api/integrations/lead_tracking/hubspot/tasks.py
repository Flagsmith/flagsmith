from django.conf import settings
from task_processor.decorators import (
    register_task_handler,
)


@register_task_handler()
def track_hubspot_lead_v2(user_id: int, organisation_id: int) -> None:
    track_hubspot_lead(user_id, organisation_id)


@register_task_handler()
def track_hubspot_lead(user_id: int, organisation_id: int | None = None) -> None:
    assert settings.ENABLE_HUBSPOT_LEAD_TRACKING

    # Avoid circular imports.
    from organisations.models import Organisation
    from users.models import FFAdminUser

    from .lead_tracker import HubspotLeadTracker

    user = FFAdminUser.objects.get(id=user_id)
    if not HubspotLeadTracker.should_track(user):
        return

    hubspot_lead_tracker = HubspotLeadTracker()

    create_lead_kwargs = {"user": user}
    if organisation_id:
        create_lead_kwargs["organisation"] = Organisation.objects.get(
            id=organisation_id
        )

    hubspot_lead_tracker.create_lead(**create_lead_kwargs)


@register_task_handler()
def create_hubspot_contact_for_user(user_id: int) -> None:
    assert settings.ENABLE_HUBSPOT_LEAD_TRACKING

    from users.models import FFAdminUser

    from .lead_tracker import HubspotLeadTracker

    user = FFAdminUser.objects.get(id=user_id)
    if not HubspotLeadTracker.should_track(user):
        return

    hubspot_lead_tracker = HubspotLeadTracker()

    hubspot_lead_tracker.create_user_hubspot_contact(user)


@register_task_handler()
def update_hubspot_active_subscription(subscription_id: int) -> None:
    assert settings.ENABLE_HUBSPOT_LEAD_TRACKING

    from organisations.models import Subscription

    from .lead_tracker import HubspotLeadTracker

    subscription = Subscription.objects.get(id=subscription_id)
    hubspot_lead_tracker = HubspotLeadTracker()
    hubspot_lead_tracker.update_company_active_subscription(subscription)


@register_task_handler()
def create_self_hosted_onboarding_lead_task(
    email: str, first_name: str, last_name: str, organisation_name: str
) -> None:
    # Avoid circular imports.
    from integrations.lead_tracking.hubspot.services import (
        create_self_hosted_onboarding_lead,
    )

    create_self_hosted_onboarding_lead(
        first_name=first_name,
        last_name=last_name,
        email=email,
        organisation_name=organisation_name,
    )
