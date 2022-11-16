from integrations.lead_tracking.pipedrive.client import PipedriveAPIClient
from integrations.lead_tracking.pipedrive.lead_tracker import (
    PipedriveLeadTracker,
)
from users.models import FFAdminUser


def test_create_lead(db, settings):
    # Given
    user = FFAdminUser.objects.create(
        first_name="Elmer", last_name="Fudd", email="elmerfudd@looneytunes.com"
    )

    settings.PIPEDRIVE_DOMAIN_ORGANIZATION_FIELD_KEY = (
        "3ba1b5f8a59b60db7b5eb29779c2fe28da8411d1"
    )
    client = PipedriveAPIClient(api_token="08e0a5d91e340bbbfcdf53d5ddbc85277794b030")
    lead_tracker = PipedriveLeadTracker(client=client)

    # When
    lead = lead_tracker.create_lead(user)

    # Then
    assert lead
