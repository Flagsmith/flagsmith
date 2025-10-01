import pytest
from pytest_mock import MockerFixture

from integrations.lead_tracking.hubspot.constants import (
    HUBSPOT_FORM_ID_SELF_HOSTED,
)
from integrations.lead_tracking.hubspot.services import (
    create_self_hosted_onboarding_lead,
)


@pytest.mark.parametrize(
    "hubspotutk, expected_hubspot_cookie", [("", False), ("test_cookie", True)]
)
def test_create_self_hosted_onboarding_lead_with_existing_company(
    mocker: MockerFixture,
    hubspotutk: str,
    expected_hubspot_cookie: str,
) -> None:
    # Given
    mocked_hubspot_client = mocker.patch(
        "integrations.lead_tracking.hubspot.services.HubspotClient", autospec=True
    )
    email = "user@flagsmith.com"
    first_name = "user"
    last_name = "test"

    # When
    create_self_hosted_onboarding_lead(email, first_name, last_name, hubspotutk)

    # Then
    mocked_hubspot_client().create_lead_form.assert_called_once()

    call_args = mocked_hubspot_client().create_lead_form.call_args
    user = call_args.kwargs["user"]
    form_id = call_args.kwargs["form_id"]

    assert user.email == email
    assert user.first_name == first_name
    assert user.last_name == last_name
    assert form_id == HUBSPOT_FORM_ID_SELF_HOSTED
    assert ("hubspot_cookie" in call_args.kwargs) is bool(hubspotutk)
