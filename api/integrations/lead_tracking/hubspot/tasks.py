from django.conf import settings

from task_processor.decorators import register_task_handler


@register_task_handler()
def track_hubspot_lead(user_id: int, organisation_id: int = None) -> None:
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
def update_hubspot_active_subscription(subscription_id: int) -> None:
    assert settings.ENABLE_HUBSPOT_LEAD_TRACKING

    from organisations.models import Subscription

    from .lead_tracker import HubspotLeadTracker

    subscription = Subscription.objects.get(id=subscription_id)
    hubspot_lead_tracker = HubspotLeadTracker()
    hubspot_lead_tracker.update_company_active_subscription(subscription)


@register_task_handler()
def track_hubspot_lead_without_organisation(user_id: int) -> None:
    """
    The Hubspot logic relies on users joining or creating an organisation
    to be tracked. This should cover most use cases, but for users that
    sign up but don't join or create an organisation we still want to be
    able to track them.
    """

    from users.models import FFAdminUser

    user = FFAdminUser.objects.get(id=user_id)
    if hasattr(user, "hubspot_lead"):
        # Since this task is designed to be delayed, there's a chance
        # that the user will have joined an organisation and thus been
        # tracked in hubspot already. If so, do nothing.
        return

    track_hubspot_lead(user.id)
