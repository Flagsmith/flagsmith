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
from integrations.lead_tracking.hubspot.lead_tracker import HubspotLeadTracker
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
    mocker.patch(
        "integrations.lead_tracking.hubspot.lead_tracker.HubspotClient",
        return_value=mock_client,
    )
    return mock_client


@responses.activate
def test_create_hubspot_contact_with_lead_form_and_get_hubspot_id(
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


def test_create_organisation_lead_skips_all_tracking_when_lead_exists(
    db: None,
    organisation: Organisation,
    mock_client_existing_contact: MagicMock,
) -> None:
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
    tracker = HubspotLeadTracker()
    tracker.create_lead(user=user, organisation=organisation)

    mock_client_existing_contact.get_contact.assert_not_called()
    mock_client_existing_contact.create_lead_form.assert_not_called()
    mock_client_existing_contact.create_company.assert_not_called()


@pytest.mark.freeze_time("2023-01-19T09:09:47+00:00")
def test_hubspot_user_org_hook_creates_hubspot_user_and_organisation_associations(
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

    mock_client_existing_contact.get_company_by_domain.return_value = {
        "id": HUBSPOT_COMPANY_ID,
        "properties": {"name": domain},
    }
    mock_client_existing_contact.update_company.return_value = {
        "id": HUBSPOT_COMPANY_ID,
        "properties": {"name": organisation.name},
    }
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
    organisation.refresh_from_db()
    assert organisation.hubspot_organisation is not None
    assert organisation.hubspot_organisation.hubspot_id == HUBSPOT_COMPANY_ID

    mock_client_existing_contact.create_company.assert_not_called()

    mock_client_existing_contact.associate_contact_to_company.assert_called_once_with(
        contact_id=HUBSPOT_USER_ID,
        company_id=HUBSPOT_COMPANY_ID,
    )
    mock_client_existing_contact.create_lead_form.assert_not_called()
    mock_client_existing_contact.get_contact.assert_called_once_with(user)


def test_create_organisation_lead_creates_contact_when_not_found_but_not_company(
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
    mock_client.associate_contact_to_company.assert_not_called()


def test_create_organisation_lead_creates_contact_for_existing_org(
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
    mock_client.associate_contact_to_company.assert_called_once_with(
        contact_id=HUBSPOT_USER_ID,
        company_id=HUBSPOT_COMPANY_ID,
    )


def test_create_organisation_lead_skips_company_for_filtered_domain(
    organisation: Organisation,
    settings: SettingsWrapper,
    mock_client_existing_contact: MagicMock,
    enable_hubspot: None,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.HUBSPOT_IGNORE_ORGANISATION_DOMAINS = ["example.com"]

    user = FFAdminUser.objects.create(
        email="new.user@example.com",
        first_name="Frank",
        last_name="Louis",
        marketing_consent_given=True,
    )

    # When
    tracker = HubspotLeadTracker()
    tracker.create_lead(user=user, organisation=organisation)

    # Then
    assert HubspotLead.objects.filter(user=user, hubspot_id=HUBSPOT_USER_ID).exists()
    mock_client_existing_contact.get_contact.assert_called_once_with(user)
    mock_client_existing_contact.create_company.assert_not_called()
    mock_client_existing_contact.associate_contact_to_company.assert_not_called()


def test_update_company_active_subscription_calls_update_company(
    db: None, mocker: MockerFixture
) -> None:
    # Given
    mock_client = mocker.MagicMock()
    mock_response = {"id": "123"}
    mock_client.update_company.return_value = mock_response

    tracker = HubspotLeadTracker()
    tracker.client = mock_client

    mock_org = mocker.MagicMock()
    mock_org.hubspot_organisation.hubspot_id = "hubspot-org-1"

    mock_subscription = mocker.MagicMock()
    mock_subscription.plan = "scaleup"
    mock_subscription.organisation = mock_org

    # When
    result = tracker.update_company_active_subscription(subscription=mock_subscription)

    # Then
    assert result == mock_response
    mock_client.update_company.assert_called_once_with(
        active_subscription="scaleup",
        hubspot_company_id="hubspot-org-1",
    )


def test_update_company_active_subscription_returns_none_when_no_hubspot_org(
    mocker: MockerFixture,
) -> None:
    # Given
    subscription = mocker.MagicMock()
    subscription.plan = "pro"
    subscription.organisation = mocker.MagicMock()
    subscription.organisation.hubspot_organisation = None

    # When
    tracker = HubspotLeadTracker()
    result = tracker.update_company_active_subscription(subscription)

    # Then
    assert result is None


def test_update_company_active_subscription_returns_none_when_no_plan(
    mocker: MockerFixture,
) -> None:
    # Given
    subscription = mocker.MagicMock()
    subscription.plan = None
    subscription.organisation = mocker.MagicMock()

    # When
    tracker = HubspotLeadTracker()
    result = tracker.update_company_active_subscription(subscription)

    # Then
    assert result is None


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
def test_create_user_hubspot_contact_retries(
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


@pytest.mark.parametrize(
    "hubspot_contact_id, hubspot_org_id",
    [
        (None, "org_123"),
        ("contact_123", None),
    ],
)
def test_create_leads_skips_association_on_missing_ids(
    mocker: MockerFixture,
    hubspot_contact_id: str | None,
    hubspot_org_id: str | None,
    staff_user: FFAdminUser,
    organisation: Organisation,
) -> None:
    # Given
    mock_client = mocker.MagicMock()
    tracker = HubspotLeadTracker()

    mocker.patch.object(
        tracker, "_get_or_create_user_hubspot_id", return_value=hubspot_contact_id
    )
    mocker.patch.object(
        tracker, "_get_organisation_hubspot_id", return_value=hubspot_org_id
    )

    # When
    tracker.create_lead(staff_user, organisation)

    # Then
    mock_client.associate_contact_to_company.assert_not_called()


def test_register_hubspot_tracker_and_track_user_fallback_to_request_user(
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
