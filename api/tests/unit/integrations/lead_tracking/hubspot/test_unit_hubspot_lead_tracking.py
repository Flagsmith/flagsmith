import datetime

from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from organisations.models import (
    HubspotOrganisation,
    Organisation,
    OrganisationRole,
)
from task_processor.task_run_method import TaskRunMethod
from users.models import FFAdminUser, HubspotLead


def test_hubspot_with_new_contact_and_new_organisation(
    organisation: Organisation,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.ENABLE_HUBSPOT_LEAD_TRACKING = True
    domain = "example.com"
    user = FFAdminUser.objects.create(
        email=f"new.user@{domain}",
        first_name="Frank",
        last_name="Louis",
        marketing_consent_given=True,
    )

    future_hubspot_id = "10280696017"
    mock_create_company = mocker.patch(
        "integrations.lead_tracking.hubspot.client.HubspotClient.create_company",
        return_value={
            "id": future_hubspot_id,
            "properties": {
                "createdate": "2024-02-26T19:41:57.959Z",
                "hs_lastmodifieddate": "2024-02-26T19:41:57.959Z",
                "hs_object_id": future_hubspot_id,
                "hs_object_source": "INTEGRATION",
                "hs_object_source_id": "2902325",
                "hs_object_source_label": "INTEGRATION",
                "name": organisation.name,
            },
            "properties_with_history": None,
            "created_at": datetime.datetime(2024, 2, 26, 19, 41, 57, 959000),
            "updated_at": datetime.datetime(2024, 2, 26, 19, 41, 57, 959000),
            "archived": False,
            "archived_at": None,
        },
    )

    mock_get_contact = mocker.patch(
        "integrations.lead_tracking.hubspot.client.HubspotClient.get_contact",
        return_value=None,
    )

    hubspot_lead_id = "1000551"
    mock_create_contact = mocker.patch(
        "integrations.lead_tracking.hubspot.client.HubspotClient.create_contact",
        return_value={
            "archived": False,
            "archived_at": None,
            "created_at": datetime.datetime(2024, 2, 26, 20, 2, 50, 69000),
            "id": hubspot_lead_id,
            "properties": {
                "createdate": "2024-02-26T20:02:50.069Z",
                "email": user.email,
                "firstname": user.first_name,
                "hs_all_contact_vids": "1000551",
                "hs_email_domain": "example.com",
                "hs_is_contact": "true",
                "hs_is_unworked": "true",
                "hs_marketable_status": user.marketing_consent_given,
                "hs_object_id": "1000551",
                "hs_object_source": "INTEGRATION",
                "hs_object_source_id": "2902325",
                "hs_object_source_label": "INTEGRATION",
                "hs_pipeline": "contacts-lifecycle-pipeline",
                "lastmodifieddate": "2024-02-26T20:02:50.069Z",
                "lastname": user.last_name,
            },
            "properties_with_history": None,
            "updated_at": datetime.datetime(2024, 2, 26, 20, 2, 50, 69000),
        },
    )

    assert getattr(organisation, "hubspot_organisation", None) is None
    # When
    user.add_organisation(organisation, role=OrganisationRole.ADMIN)

    # Then
    assert HubspotLead.objects.filter(hubspot_id=hubspot_lead_id).exists() is True
    organisation.refresh_from_db()
    assert organisation.hubspot_organisation.hubspot_id == future_hubspot_id

    mock_create_company.assert_called_once_with(
        name=organisation.name,
        domain=domain,
        active_subscription="free",
        organisation_id=organisation.id,
    )
    mock_create_contact.assert_called_once_with(user, future_hubspot_id)
    mock_get_contact.assert_called_once_with(user)


def test_hubspot_with_filtered_email_domain_contact_and_new_organisation(
    organisation: Organisation,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.ENABLE_HUBSPOT_LEAD_TRACKING = True
    domain = "example.com"

    # Setting that will filter out the domain for the user.
    settings.HUBSPOT_IGNORE_ORGANISATION_DOMAINS = [domain]

    user = FFAdminUser.objects.create(
        email=f"new.user@{domain}",
        first_name="Frank",
        last_name="Louis",
        marketing_consent_given=True,
    )

    future_hubspot_id = "10280696017"
    mock_create_company = mocker.patch(
        "integrations.lead_tracking.hubspot.client.HubspotClient.create_company",
        return_value={
            "id": future_hubspot_id,
            "properties": {
                "createdate": "2024-02-26T19:41:57.959Z",
                "hs_lastmodifieddate": "2024-02-26T19:41:57.959Z",
                "hs_object_id": future_hubspot_id,
                "hs_object_source": "INTEGRATION",
                "hs_object_source_id": "2902325",
                "hs_object_source_label": "INTEGRATION",
                "name": organisation.name,
            },
            "properties_with_history": None,
            "created_at": datetime.datetime(2024, 2, 26, 19, 41, 57, 959000),
            "updated_at": datetime.datetime(2024, 2, 26, 19, 41, 57, 959000),
            "archived": False,
            "archived_at": None,
        },
    )

    mock_get_contact = mocker.patch(
        "integrations.lead_tracking.hubspot.client.HubspotClient.get_contact",
        return_value=None,
    )

    mock_create_contact = mocker.patch(
        "integrations.lead_tracking.hubspot.client.HubspotClient.create_contact",
        return_value={
            "archived": False,
            "archived_at": None,
            "created_at": datetime.datetime(2024, 2, 26, 20, 2, 50, 69000),
            "id": "1000551",
            "properties": {
                "createdate": "2024-02-26T20:02:50.069Z",
                "email": user.email,
                "firstname": user.first_name,
                "hs_all_contact_vids": "1000551",
                "hs_email_domain": "example.com",
                "hs_is_contact": "true",
                "hs_is_unworked": "true",
                "hs_marketable_status": user.marketing_consent_given,
                "hs_object_id": "1000551",
                "hs_object_source": "INTEGRATION",
                "hs_object_source_id": "2902325",
                "hs_object_source_label": "INTEGRATION",
                "hs_pipeline": "contacts-lifecycle-pipeline",
                "lastmodifieddate": "2024-02-26T20:02:50.069Z",
                "lastname": user.last_name,
            },
            "properties_with_history": None,
            "updated_at": datetime.datetime(2024, 2, 26, 20, 2, 50, 69000),
        },
    )

    assert getattr(organisation, "hubspot_organisation", None) is None
    # When
    user.add_organisation(organisation, role=OrganisationRole.ADMIN)

    # Then
    organisation.refresh_from_db()
    assert organisation.hubspot_organisation.hubspot_id == future_hubspot_id
    # Domain is `None` since it was filtered out.
    mock_create_company.assert_called_once_with(
        name=organisation.name,
        domain=None,
        active_subscription="free",
        organisation_id=organisation.id,
    )
    mock_create_contact.assert_called_once_with(user, future_hubspot_id)
    mock_get_contact.assert_called_once_with(user)


def test_hubspot_with_new_contact_and_existing_organisation(
    organisation: Organisation,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.ENABLE_HUBSPOT_LEAD_TRACKING = True
    user = FFAdminUser.objects.create(
        email="new.user@example.com",
        first_name="Frank",
        last_name="Louis",
        marketing_consent_given=True,
    )
    hubspot_id = "10280696017"

    # Create an existing hubspot organisation to mimic a previous
    # successful API call with a different lead.
    HubspotOrganisation.objects.create(organisation=organisation, hubspot_id=hubspot_id)

    mock_create_company = mocker.patch(
        "integrations.lead_tracking.hubspot.client.HubspotClient.create_company"
    )
    mock_get_contact = mocker.patch(
        "integrations.lead_tracking.hubspot.client.HubspotClient.get_contact",
        return_value=None,
    )

    hubspot_lead_id = "1000551"
    mock_create_contact = mocker.patch(
        "integrations.lead_tracking.hubspot.client.HubspotClient.create_contact",
        return_value={
            "archived": False,
            "archived_at": None,
            "created_at": datetime.datetime(2024, 2, 26, 20, 2, 50, 69000),
            "id": hubspot_lead_id,
            "properties": {
                "createdate": "2024-02-26T20:02:50.069Z",
                "email": user.email,
                "firstname": user.first_name,
                "hs_all_contact_vids": "1000551",
                "hs_email_domain": "example.com",
                "hs_is_contact": "true",
                "hs_is_unworked": "true",
                "hs_marketable_status": user.marketing_consent_given,
                "hs_object_id": "1000551",
                "hs_object_source": "INTEGRATION",
                "hs_object_source_id": "2902325",
                "hs_object_source_label": "INTEGRATION",
                "hs_pipeline": "contacts-lifecycle-pipeline",
                "lastmodifieddate": "2024-02-26T20:02:50.069Z",
                "lastname": user.last_name,
            },
            "properties_with_history": None,
            "updated_at": datetime.datetime(2024, 2, 26, 20, 2, 50, 69000),
        },
    )

    # When
    user.add_organisation(organisation, role=OrganisationRole.ADMIN)

    # Then
    assert HubspotLead.objects.filter(hubspot_id=hubspot_lead_id).exists() is True
    mock_create_company.assert_not_called()
    mock_create_contact.assert_called_once_with(user, hubspot_id)
    mock_get_contact.assert_called_once_with(user)


def test_hubspot_with_existing_contact_and_new_organisation(
    organisation: Organisation,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    settings.ENABLE_HUBSPOT_LEAD_TRACKING = True
    user = FFAdminUser.objects.create(
        email="new.user@example.com",
        first_name="Frank",
        last_name="Louis",
        marketing_consent_given=True,
    )

    mock_create_company = mocker.patch(
        "integrations.lead_tracking.hubspot.client.HubspotClient.create_company"
    )
    mock_create_contact = mocker.patch(
        "integrations.lead_tracking.hubspot.client.HubspotClient.create_contact"
    )

    mock_get_contact = mocker.patch(
        "integrations.lead_tracking.hubspot.client.HubspotClient.get_contact",
        return_value=[
            {
                "archived": False,
                "archived_at": None,
                "created_at": datetime.datetime(2024, 2, 26, 20, 2, 50, 69000),
                "id": "1000551",
                "properties": {
                    "createdate": "2024-02-26T20:02:50.069Z",
                    "email": user.email,
                    "firstname": user.first_name,
                    "hs_object_id": "1000551",
                    "lastmodifieddate": "2024-02-26T20:03:25.254Z",
                    "lastname": user.last_name,
                },
                "properties_with_history": None,
                "updated_at": datetime.datetime(2024, 2, 26, 20, 3, 25, 254000),
            }
        ],
    )

    # When
    user.add_organisation(organisation, role=OrganisationRole.ADMIN)

    # Then
    organisation.refresh_from_db()
    assert getattr(organisation, "hubspot_organisation", None) is None
    mock_get_contact.assert_called_once_with(user)

    # Since the user already exists as a lead, don't create any
    # further hubspot resources.
    mock_create_company.assert_not_called()
    mock_create_contact.assert_not_called()


def test_update_company_active_subscription(
    organisation: Organisation,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    settings.ENABLE_HUBSPOT_LEAD_TRACKING = True
    settings.TASK_RUN_METHOD = TaskRunMethod.SYNCHRONOUSLY

    mock_update_company = mocker.patch(
        "integrations.lead_tracking.hubspot.client.HubspotClient.update_company"
    )
    hubspot_id = "12345"
    # Create an existing hubspot organisation to mimic a previous
    # successful API call.
    HubspotOrganisation.objects.create(
        organisation=organisation,
        hubspot_id=hubspot_id,
    )

    assert organisation.subscription.plan == "free"

    # When
    organisation.subscription.plan = "scale-up-v2"
    organisation.subscription.save()

    # Then
    mock_update_company.assert_called_once_with(
        active_subscription=organisation.subscription.plan,
        hubspot_company_id=hubspot_id,
    )


def test_update_company_active_subscription_not_called(
    organisation: Organisation,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Set to False to ensure update doesn't happen.
    settings.ENABLE_HUBSPOT_LEAD_TRACKING = False
    settings.TASK_RUN_METHOD = TaskRunMethod.SYNCHRONOUSLY

    mock_update_company = mocker.patch(
        "integrations.lead_tracking.hubspot.client.HubspotClient.update_company"
    )
    hubspot_id = "12345"
    # Create an existing hubspot organisation to mimic a previous
    # successful API call.
    HubspotOrganisation.objects.create(
        organisation=organisation,
        hubspot_id=hubspot_id,
    )

    assert organisation.subscription.plan == "free"

    # When
    organisation.subscription.plan = "scale-up-v2"
    organisation.subscription.save()

    # Then
    mock_update_company.assert_not_called()
