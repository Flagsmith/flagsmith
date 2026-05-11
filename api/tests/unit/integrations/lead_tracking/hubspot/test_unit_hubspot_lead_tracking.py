import typing
from datetime import timedelta
from unittest.mock import MagicMock

import pytest
import responses
from django.utils import timezone
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from rest_framework.test import APIRequestFactory
from task_processor.task_run_method import TaskRunMethod

from integrations.lead_tracking.hubspot.constants import (
    HUBSPOT_FORM_ID_SAAS,
    HUBSPOT_PORTAL_ID,
    HUBSPOT_ROOT_FORM_URL,
)
from integrations.lead_tracking.hubspot.lead_tracker import (
    HubspotLeadTracker,
    _company_domain_from_email,
)
from integrations.lead_tracking.hubspot.services import (
    register_hubspot_tracker_and_track_user,
)
from integrations.lead_tracking.hubspot.tasks import track_hubspot_lead_v2
from organisations.models import (
    HubspotOrganisation,
    Organisation,
    OrganisationRole,
)
from users.models import FFAdminUser, HubspotLead, HubspotTracker

HUBSPOT_USER_ID = "1000551"
HUBSPOT_COMPANY_ID = "10280696017"


@pytest.fixture()
def hubspot_access_token() -> str:
    return "foobar"


@pytest.fixture()
def enable_hubspot(settings: SettingsWrapper, hubspot_access_token: str) -> None:
    settings.ENABLE_HUBSPOT_LEAD_TRACKING = True
    settings.HUBSPOT_ACCESS_TOKEN = hubspot_access_token
    settings.TASK_RUN_METHOD = TaskRunMethod.SYNCHRONOUSLY


@pytest.fixture()
def mock_client_existing_contact(mocker: MockerFixture) -> MagicMock:
    mock_client: MagicMock = mocker.MagicMock()
    mock_client.get_contact.return_value = {"id": HUBSPOT_USER_ID}
    mock_client.create_contact.return_value = {"id": HUBSPOT_USER_ID}
    mock_client.create_lead_form.return_value = None
    mock_client.create_company.return_value = {
        "id": HUBSPOT_COMPANY_ID,
    }
    # Default to no company match - tests that need a matched company should
    # override this on the returned mock.
    mock_client.get_company_by_domain.return_value = None
    mocker.patch(
        "integrations.lead_tracking.hubspot.lead_tracker.HubspotClient",
        return_value=mock_client,
    )
    return mock_client


@responses.activate
def test_create_user_hubspot_contact__new_user_with_tracker__returns_hubspot_id(
    db: None,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.ENABLE_HUBSPOT_LEAD_TRACKING = False
    domain = "example.com"
    user = FFAdminUser.objects.create(
        email=f"new.user@{domain}",
        first_name="Frank",
        last_name="Louis",
        marketing_consent_given=True,
    )
    tracker_cookie = "abc123"
    HubspotTracker.objects.create(user=user, hubspot_cookie=tracker_cookie)
    responses.add(
        responses.POST,
        f"{HUBSPOT_ROOT_FORM_URL}/{HUBSPOT_PORTAL_ID}/{HUBSPOT_FORM_ID_SAAS}",
        json={},
        status=200,
        match=[responses.matchers.header_matcher({"Content-Type": "application/json"})],
    )
    mocker.patch(
        "integrations.lead_tracking.hubspot.client.HubspotClient.get_contact",
        return_value={"id": HUBSPOT_USER_ID},
    )
    # When
    tracker = HubspotLeadTracker()
    hubspot_id = tracker.create_user_hubspot_contact(user)
    # Then
    assert HubspotLead.objects.filter(hubspot_id=hubspot_id).exists() is True
    assert hubspot_id == HUBSPOT_USER_ID


def test_create_lead__existing_hubspot_lead_and_org__skips_all_tracking(
    db: None,
    organisation: Organisation,
    mock_client_existing_contact: MagicMock,
) -> None:
    # Given
    user = FFAdminUser.objects.create(
        email="existing.lead@example.com",
        first_name="Jane",
        last_name="Doe",
        marketing_consent_given=True,
    )
    HubspotLead.objects.create(user=user, hubspot_id=HUBSPOT_USER_ID)
    HubspotOrganisation.objects.create(
        organisation=organisation,
        hubspot_id=HUBSPOT_COMPANY_ID,
    )
    # When
    tracker = HubspotLeadTracker()
    tracker.create_lead(user=user, organisation=organisation)

    # Then
    mock_client_existing_contact.get_contact.assert_not_called()
    mock_client_existing_contact.create_lead_form.assert_not_called()
    mock_client_existing_contact.create_company.assert_not_called()


@pytest.mark.freeze_time("2023-01-19T09:09:47+00:00")
def test_track_hubspot_lead_v2__new_user_added_to_org__creates_associations(
    organisation: Organisation,
    enable_hubspot: None,
    mock_client_existing_contact: MagicMock,
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given
    domain = "example.com"
    settings.ENABLE_HUBSPOT_LEAD_TRACKING = True
    user = FFAdminUser.objects.create(
        email=f"new.user@{domain}",
        first_name="Frank",
        last_name="Louis",
        marketing_consent_given=True,
    )
    HubspotTracker.objects.create(user=user, hubspot_cookie="tracker")

    mock_track_hubspot_lead_v2 = mocker.patch(
        "organisations.models.track_hubspot_lead_v2"
    )

    assert getattr(organisation, "hubspot_organisation", None) is None
    # When
    user.add_organisation(organisation, role=OrganisationRole.ADMIN)

    # Then
    mock_track_hubspot_lead_v2.delay.assert_called_once_with(
        args=(user.id, organisation.id),
        delay_until=timezone.now() + timedelta(minutes=3),
    )

    # Triggering it manually to void the delay
    track_hubspot_lead_v2(user.id, organisation.id)

    # create_lead only creates the contact, not the company association
    mock_client_existing_contact.create_company.assert_not_called()
    mock_client_existing_contact.create_lead_form.assert_not_called()
    mock_client_existing_contact.get_contact.assert_called_once_with(user)


def test_create_lead__contact_not_found_initially__creates_contact_via_form(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    # Given
    user = FFAdminUser.objects.create(
        email="new.user@example.com",
        first_name="Frank",
        last_name="Louis",
        marketing_consent_given=True,
    )

    mock_client = mocker.MagicMock()
    mock_client.get_contact.side_effect = [None, {"id": HUBSPOT_USER_ID}]
    mock_client.create_lead_form.return_value = {}
    mock_client.create_company.return_value = {"id": HUBSPOT_COMPANY_ID}
    mock_client.get_company_by_domain.return_value = None
    mocker.patch(
        "integrations.lead_tracking.hubspot.lead_tracker.HubspotLeadTracker._get_client",
        return_value=mock_client,
    )

    # When
    tracker = HubspotLeadTracker()
    tracker.create_lead(user=user, organisation=organisation)

    # Then
    hubspot_lead = HubspotLead.objects.get(user=user)
    assert hubspot_lead is not None
    assert hubspot_lead.hubspot_id == HUBSPOT_USER_ID

    assert mock_client.get_contact.call_count == 2
    mock_client.create_lead_form.assert_called_once_with(
        user=user, form_id=HUBSPOT_FORM_ID_SAAS
    )
    mock_client.create_company.assert_not_called()  # We rely on Hubspot creating contacts


def test_create_lead__existing_hubspot_org__creates_contact_without_association(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    # Given
    user = FFAdminUser.objects.create(
        email="new.user@example.com",
        first_name="Frank",
        last_name="Louis",
        marketing_consent_given=True,
    )

    HubspotOrganisation.objects.create(
        organisation=organisation, hubspot_id=HUBSPOT_COMPANY_ID
    )

    mock_client = mocker.MagicMock()
    mock_client.get_contact.side_effect = [None, {"id": HUBSPOT_USER_ID}]
    mock_client.create_lead_form.return_value = {}
    mocker.patch(
        "integrations.lead_tracking.hubspot.lead_tracker.HubspotLeadTracker._get_client",
        return_value=mock_client,
    )

    # When
    tracker = HubspotLeadTracker()
    tracker.create_lead(user=user, organisation=organisation)

    # Then
    assert HubspotLead.objects.filter(user=user, hubspot_id=HUBSPOT_USER_ID).exists()
    mock_client.create_company.assert_not_called()
    assert mock_client.get_contact.call_count == 2
    mock_client.create_lead_form.assert_called_once_with(
        user=user, form_id=HUBSPOT_FORM_ID_SAAS
    )


@pytest.mark.parametrize(
    "get_contact_return_values, expected_call_count, expected_hubspot_id, hubspot_leads_exists",
    [
        ([{"id": HUBSPOT_USER_ID}, None, None], 1, HUBSPOT_USER_ID, True),
        ([None, {"id": HUBSPOT_USER_ID}, None, None], 2, HUBSPOT_USER_ID, True),
        ([None, None, {"id": HUBSPOT_USER_ID}, None], 3, HUBSPOT_USER_ID, True),
        ([None, None, None, None], 4, None, False),
        ([None, None, None, None, None, None, None, None], 4, None, False),
    ],
)
def test_create_user_hubspot_contact__get_contact_retries__returns_expected_id(
    db: None,
    mocker: MockerFixture,
    get_contact_return_values: list[dict[str, typing.Any] | None],
    expected_call_count: int,
    expected_hubspot_id: str | None,
    hubspot_leads_exists: bool,
) -> None:
    # Given
    user = FFAdminUser.objects.create(
        email="test@example.com", first_name="John", last_name="Doe"
    )

    mock_client = mocker.MagicMock()
    mock_client.get_contact.side_effect = get_contact_return_values
    mocker.patch("time.sleep", return_value=None)
    tracker = HubspotLeadTracker()
    tracker.client = mock_client

    # When
    hubspot_id = tracker.create_user_hubspot_contact(user)

    # Then
    assert hubspot_id == expected_hubspot_id
    assert (
        HubspotLead.objects.filter(hubspot_id=hubspot_id).exists()
        is hubspot_leads_exists
    )
    assert mock_client.get_contact.call_count == expected_call_count


@pytest.mark.parametrize("email", ["", "no-at-symbol", None])
def test_company_domain_from_email__malformed_input__returns_none(
    email: str | None,
) -> None:
    """Defensive return-None on empty/malformed email - protects against
    callers that bypass the Django EmailField validation."""
    assert _company_domain_from_email(email) is None  # type: ignore[arg-type]


def test_create_lead__corporate_email_with_matching_company__writes_orgid_only(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    """The orgid_unique write must contain ONLY the org id - no name, no
    subscription. This is the regression guard for PR #7147 which bundled
    these together and was later reverted because the bundle was wrong."""
    # Given
    user = FFAdminUser.objects.create(
        email="user@example.com",
        first_name="Frank",
        last_name="Louis",
        marketing_consent_given=True,
    )
    HubspotLead.objects.create(user=user, hubspot_id=HUBSPOT_USER_ID)

    mock_client = mocker.MagicMock()
    mock_client.get_company_by_domain.return_value = {"id": HUBSPOT_COMPANY_ID}
    mocker.patch(
        "integrations.lead_tracking.hubspot.lead_tracker.HubspotLeadTracker._get_client",
        return_value=mock_client,
    )

    # When
    tracker = HubspotLeadTracker()
    tracker.create_lead(user=user, organisation=organisation)

    # Then
    mock_client.get_company_by_domain.assert_called_once_with("example.com")
    mock_client.update_company.assert_called_once_with(
        hubspot_company_id=HUBSPOT_COMPANY_ID,
        flagsmith_organisation_id=organisation.id,
    )
    # Regression: must NOT pass a name or subscription - these were the two
    # things that made the previous integration overwrite enriched data.
    call_kwargs = mock_client.update_company.call_args.kwargs
    assert "name" not in call_kwargs
    assert "active_subscription" not in call_kwargs
    # The HubspotOrganisation row should be persisted so we do not re-write.
    assert HubspotOrganisation.objects.filter(
        organisation=organisation, hubspot_id=HUBSPOT_COMPANY_ID
    ).exists()


def test_create_lead__existing_hubspot_organisation__skips_company_lookup(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    """Once a Flagsmith organisation is linked to a HubSpot company we do not
    re-write the orgid (which would burn API calls and risk overwriting if
    multiple Flagsmith orgs share a company)."""
    # Given
    user = FFAdminUser.objects.create(
        email="user@example.com",
        first_name="Frank",
        last_name="Louis",
        marketing_consent_given=True,
    )
    HubspotLead.objects.create(user=user, hubspot_id=HUBSPOT_USER_ID)
    HubspotOrganisation.objects.create(
        organisation=organisation, hubspot_id=HUBSPOT_COMPANY_ID
    )

    mock_client = mocker.MagicMock()
    mocker.patch(
        "integrations.lead_tracking.hubspot.lead_tracker.HubspotLeadTracker._get_client",
        return_value=mock_client,
    )

    # When
    tracker = HubspotLeadTracker()
    tracker.create_lead(user=user, organisation=organisation)

    # Then
    mock_client.get_company_by_domain.assert_not_called()
    mock_client.update_company.assert_not_called()


@pytest.mark.parametrize(
    "email",
    [
        "user@gmail.com",
        "user@yahoo.com",
        "user@hotmail.com",
        "user@outlook.com",
        "user@proton.me",
    ],
)
def test_create_lead__generic_email_domain__skips_orgid_write(
    organisation: Organisation,
    mocker: MockerFixture,
    email: str,
) -> None:
    """Personal email domains do not identify a unique company so we skip
    the company lookup entirely."""
    # Given
    user = FFAdminUser.objects.create(
        email=email,
        first_name="Frank",
        last_name="Louis",
        marketing_consent_given=True,
    )
    HubspotLead.objects.create(user=user, hubspot_id=HUBSPOT_USER_ID)

    mock_client = mocker.MagicMock()
    mocker.patch(
        "integrations.lead_tracking.hubspot.lead_tracker.HubspotLeadTracker._get_client",
        return_value=mock_client,
    )

    # When
    tracker = HubspotLeadTracker()
    tracker.create_lead(user=user, organisation=organisation)

    # Then
    mock_client.get_company_by_domain.assert_not_called()
    mock_client.update_company.assert_not_called()
    assert not HubspotOrganisation.objects.filter(organisation=organisation).exists()


def test_create_lead__no_hubspot_company_for_domain__skips_update(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    """If HubSpot has not yet auto-created a company for the user's domain we
    skip the update silently - the next user joining the same org will retry."""
    # Given
    user = FFAdminUser.objects.create(
        email="user@example.com",
        first_name="Frank",
        last_name="Louis",
        marketing_consent_given=True,
    )
    HubspotLead.objects.create(user=user, hubspot_id=HUBSPOT_USER_ID)

    mock_client = mocker.MagicMock()
    mock_client.get_company_by_domain.return_value = None
    mocker.patch(
        "integrations.lead_tracking.hubspot.lead_tracker.HubspotLeadTracker._get_client",
        return_value=mock_client,
    )

    # When
    tracker = HubspotLeadTracker()
    tracker.create_lead(user=user, organisation=organisation)

    # Then
    mock_client.update_company.assert_not_called()
    assert not HubspotOrganisation.objects.filter(organisation=organisation).exists()


def test_register_hubspot_tracker_and_track_user__no_explicit_user__falls_back_to_request_user(
    mocker: MockerFixture, staff_user: FFAdminUser, settings: SettingsWrapper
) -> None:
    # Given
    settings.ENABLE_HUBSPOT_LEAD_TRACKING = True

    mock_register_hubspot_tracker = mocker.patch(
        "integrations.lead_tracking.hubspot.services.register_hubspot_tracker"
    )
    mock_create_hubspot_contact_for_user = mocker.patch(
        "integrations.lead_tracking.hubspot.services.create_hubspot_contact_for_user"
    )

    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = staff_user

    # When
    register_hubspot_tracker_and_track_user(request)

    # Then
    mock_register_hubspot_tracker.assert_called_once_with(request, None)
    mock_create_hubspot_contact_for_user.delay.assert_called_once_with(
        args=(staff_user.id,)
    )
