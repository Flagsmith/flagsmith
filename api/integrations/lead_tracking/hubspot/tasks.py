from django.conf import settings

from task_processor.decorators import register_task_handler


@register_task_handler()
def track_hubspot_lead(user_id: int, organisation_id: int) -> None:
    assert settings.ENABLE_HUBSPOT_LEAD_TRACKING

    # Avoid circular imports.
    from organisations.models import Organisation
    from users.models import FFAdminUser

    from .lead_tracker import HubspotLeadTracker

    user = FFAdminUser.objects.get(id=user_id)

    if not HubspotLeadTracker.should_track(user):
        return

    organisation = Organisation.objects.get(id=organisation_id)

    hubspot_lead_tracker = HubspotLeadTracker()
    hubspot_lead_tracker.create_lead(user=user, organisation=organisation)
