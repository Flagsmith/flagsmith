from pytest_mock import MockerFixture

from integrations.lead_tracking.hubspot.tasks import (
    track_hubspot_lead_without_organisation,
)
from users.models import FFAdminUser


def test_track_hubspot_lead_without_organisation(mocker: MockerFixture) -> None:
    # Given
    user = FFAdminUser.objects.create(email="test@example.com")

    mocker.patch(
        "integrations.lead_tracking.hubspot.client.HubspotClient.get_contact",
        return_value=None,
    )

    # When
    track_hubspot_lead_without_organisation(user_id=user.id)

    # Then
    # TODO
