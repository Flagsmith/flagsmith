import pytest

from integrations.lead_tracking.pipedrive.constants import MarketingStatus
from integrations.lead_tracking.pipedrive.exceptions import (
    MultipleMatchingOrganizationsError,
)
from integrations.lead_tracking.pipedrive.lead_tracker import (
    PipedriveLeadTracker,
)
from integrations.lead_tracking.pipedrive.models import (
    PipedriveOrganization,
    PipedrivePerson,
)
from organisations.models import Organisation, Subscription
from users.models import FFAdminUser, SignUpType


def test_create_lead_adds_to_existing_organization_if_exists(db, mocker, settings):  # type: ignore[no-untyped-def]
    # Given
    user = FFAdminUser.objects.create(
        email="elmerfudd@looneytunes.com", sign_up_type=SignUpType.NO_INVITE.value
    )
    settings.PIPEDRIVE_SIGN_UP_TYPE_DEAL_FIELD_KEY = "key1"
    settings.PIPEDRIVE_API_LEAD_SOURCE_DEAL_FIELD_KEY = "key2"

    organization = PipedriveOrganization(name="some-org", id=1)
    mock_pipedrive_client = mocker.MagicMock()
    mock_pipedrive_client.search_organizations.return_value = [organization]

    person = PipedrivePerson(id=1, name="Elmer Fudd")
    mock_pipedrive_client.search_persons.return_value = [person]

    lead_tracker = PipedriveLeadTracker(client=mock_pipedrive_client)

    # When
    lead_tracker.create_lead(user)

    # Then
    expected_create_lead_kwargs = {
        "title": user.email,
        "organization_id": organization.id,
        "label_ids": [],
        "custom_fields": {
            settings.PIPEDRIVE_SIGN_UP_TYPE_DEAL_FIELD_KEY: SignUpType.NO_INVITE.value,
            settings.PIPEDRIVE_API_LEAD_SOURCE_DEAL_FIELD_KEY: settings.PIPEDRIVE_API_LEAD_SOURCE_VALUE,
        },
        "person_id": person.id,
    }
    mock_pipedrive_client.create_lead.assert_called_once_with(
        **expected_create_lead_kwargs
    )
    mock_pipedrive_client.create_organization.assert_not_called()


def test_create_lead_creates_new_organization_if_not_exists(db, settings, mocker):  # type: ignore[no-untyped-def]
    # Given
    domain_organization_field_key = "domain-organization-field-key"
    settings.PIPEDRIVE_DOMAIN_ORGANIZATION_FIELD_KEY = domain_organization_field_key
    settings.PIPEDRIVE_SIGN_UP_TYPE_DEAL_FIELD_KEY = "key1"
    settings.PIPEDRIVE_API_LEAD_SOURCE_DEAL_FIELD_KEY = "key2"

    user = FFAdminUser.objects.create(
        email="elmerfudd@looneytunes.com", sign_up_type=SignUpType.NO_INVITE.value
    )

    organization = PipedriveOrganization(name="some-org", id=1)
    mock_pipedrive_client = mocker.MagicMock()
    mock_pipedrive_client.search_organizations.return_value = []
    mock_pipedrive_client.create_organization.return_value = organization

    person = PipedrivePerson(id=1, name="Elmer Fudd")
    mock_pipedrive_client.search_persons.return_value = [person]

    lead_tracker = PipedriveLeadTracker(client=mock_pipedrive_client)

    # When
    lead_tracker.create_lead(user)

    # Then
    expected_create_lead_kwargs = {
        "title": user.email,
        "organization_id": organization.id,
        "label_ids": [],
        "custom_fields": {
            settings.PIPEDRIVE_SIGN_UP_TYPE_DEAL_FIELD_KEY: SignUpType.NO_INVITE.value,
            settings.PIPEDRIVE_API_LEAD_SOURCE_DEAL_FIELD_KEY: settings.PIPEDRIVE_API_LEAD_SOURCE_VALUE,
        },
        "person_id": person.id,
    }
    mock_pipedrive_client.create_lead.assert_called_once_with(
        **expected_create_lead_kwargs
    )
    mock_pipedrive_client.create_organization.assert_called_once_with(
        name="looneytunes",
        organization_fields={domain_organization_field_key: "looneytunes.com"},
    )


def test_create_lead_throws_exception_if_multiple_organisations_found(  # type: ignore[no-untyped-def]
    db, settings, mocker
):
    # Given
    user = FFAdminUser(email="elmerfudd@looneytunes.com")

    organization_1 = PipedriveOrganization(name="some-org-1", id=1)
    organization_2 = PipedriveOrganization(name="some-org-2", id=2)
    mock_pipedrive_client = mocker.MagicMock()
    mock_pipedrive_client.search_organizations.return_value = [
        organization_1,
        organization_2,
    ]

    lead_tracker = PipedriveLeadTracker(client=mock_pipedrive_client)

    # When
    with pytest.raises(MultipleMatchingOrganizationsError):
        lead_tracker.create_lead(user)

    # Then
    mock_pipedrive_client.create_lead.assert_not_called()


@pytest.mark.parametrize(
    "user_domain, regex, expected_result",
    (
        ("example.com", None, True),
        ("example.com", r"example.com", False),
        ("example.io", r"example\..*", False),
    ),
)
def test_pipedrive_lead_tracker_should_track_ignore_domains_regex(  # type: ignore[no-untyped-def]
    user_domain, regex, expected_result, settings, django_user_model, mocker
):
    # Given
    mock_pipedrive_client = mocker.MagicMock()
    mocker.patch(
        "integrations.lead_tracking.pipedrive.lead_tracker.PipedriveAPIClient",
        return_value=mock_pipedrive_client,
    )

    settings.PIPEDRIVE_IGNORE_DOMAINS_REGEX = regex
    settings.ENABLE_PIPEDRIVE_LEAD_TRACKING = True

    user = django_user_model.objects.create(email=f"test@{user_domain}")

    # When
    result = PipedriveLeadTracker.should_track(user)

    # Then
    assert result is expected_result


@pytest.mark.parametrize(
    "user_domain, ignore_domains, expected_result",
    (("gmail.com", [], True), ("gmail.com", ["gmail.com"], False)),
)
def test_pipedrive_lead_tracker_should_track_ignore_domains(  # type: ignore[no-untyped-def]
    user_domain, ignore_domains, expected_result, settings, django_user_model, mocker
):
    # Given
    mock_pipedrive_client = mocker.MagicMock()
    mocker.patch(
        "integrations.lead_tracking.pipedrive.lead_tracker.PipedriveAPIClient",
        return_value=mock_pipedrive_client,
    )

    settings.PIPEDRIVE_IGNORE_DOMAINS = ignore_domains
    settings.ENABLE_PIPEDRIVE_LEAD_TRACKING = True

    user = django_user_model.objects.create(email=f"test@{user_domain}")

    # When
    result = PipedriveLeadTracker.should_track(user)

    # Then
    assert result is expected_result


def test_pipedrive_lead_tracker_should_track_false_if_user_belongs_to_paid_organisation(  # type: ignore[no-untyped-def]  # noqa: E501
    settings, django_user_model, organisation, chargebee_subscription, mocker
):
    # Given
    mock_pipedrive_client = mocker.MagicMock()
    mocker.patch(
        "integrations.lead_tracking.pipedrive.lead_tracker.PipedriveAPIClient",
        return_value=mock_pipedrive_client,
    )

    settings.ENABLE_PIPEDRIVE_LEAD_TRACKING = True

    user = django_user_model.objects.create(email="test@example.com")
    user.organisations.add(organisation)

    # When
    result = PipedriveLeadTracker.should_track(user)

    # Then
    assert result is False


def test_create_lead_creates_person_if_none_found(db, mocker, settings):  # type: ignore[no-untyped-def]
    # Given
    user = FFAdminUser.objects.create(
        email="elmerfudd@looneytunes.com", sign_up_type=SignUpType.NO_INVITE.value
    )
    settings.PIPEDRIVE_SIGN_UP_TYPE_DEAL_FIELD_KEY = "key1"
    settings.PIPEDRIVE_API_LEAD_SOURCE_DEAL_FIELD_KEY = "key2"

    organization = PipedriveOrganization(name="some-org", id=1)
    mock_pipedrive_client = mocker.MagicMock()
    mock_pipedrive_client.search_organizations.return_value = [organization]

    person = PipedrivePerson(id=1, name="Elmer Fudd")
    mock_pipedrive_client.search_persons.return_value = []
    mock_pipedrive_client.create_person.return_value = person

    lead_tracker = PipedriveLeadTracker(client=mock_pipedrive_client)

    # When
    lead_tracker.create_lead(user)

    # Then
    expected_create_lead_kwargs = {
        "title": user.email,
        "organization_id": organization.id,
        "label_ids": [],
        "custom_fields": {
            settings.PIPEDRIVE_SIGN_UP_TYPE_DEAL_FIELD_KEY: SignUpType.NO_INVITE.value,
            settings.PIPEDRIVE_API_LEAD_SOURCE_DEAL_FIELD_KEY: settings.PIPEDRIVE_API_LEAD_SOURCE_VALUE,
        },
        "person_id": person.id,
    }
    mock_pipedrive_client.create_lead.assert_called_once_with(
        **expected_create_lead_kwargs
    )
    mock_pipedrive_client.create_organization.assert_not_called()
    mock_pipedrive_client.create_person.assert_called_once_with(
        user.full_name, user.email, MarketingStatus.NO_CONSENT
    )


def test_create_lead_adds_existing_customer_label_if_organisation_is_paid(  # type: ignore[no-untyped-def]
    db, mocker, settings
):
    # Given
    user = FFAdminUser.objects.create(
        email="elmerfudd@looneytunes.com", sign_up_type=SignUpType.NO_INVITE.value
    )
    organisation = Organisation.objects.create(name="Test org")
    Subscription.objects.update_or_create(
        organisation=organisation, defaults={"subscription_id": "some-id"}
    )
    user.add_organisation(organisation)

    pipedrive_lead_label_existing_customer_id = "some-id"
    settings.PIPEDRIVE_LEAD_LABEL_EXISTING_CUSTOMER_ID = (
        pipedrive_lead_label_existing_customer_id
    )

    organization = PipedriveOrganization(name=organisation.name, id=1)
    mock_pipedrive_client = mocker.MagicMock()
    mock_pipedrive_client.search_organizations.return_value = [organization]

    person = PipedrivePerson(id=1, name="Elmer Fudd")
    mock_pipedrive_client.search_persons.return_value = [person]

    lead_tracker = PipedriveLeadTracker(client=mock_pipedrive_client)

    # When
    lead_tracker.create_lead(user)

    # Then
    expected_create_lead_kwargs = {
        "title": user.email,
        "custom_fields": {},
        "organization_id": organization.id,
        "label_ids": [pipedrive_lead_label_existing_customer_id],
        "person_id": person.id,
    }
    mock_pipedrive_client.create_lead.assert_called_once_with(
        **expected_create_lead_kwargs
    )
    mock_pipedrive_client.create_organization.assert_not_called()


@pytest.mark.parametrize(
    "subscription_id, label_id, expected_label_ids",
    (("subscription-id", "label-id", ["label-id"]), (None, "label-id", [])),
)
def test_get_label_ids_for_user(  # type: ignore[no-untyped-def]
    db, settings, subscription_id, label_id, expected_label_ids
):
    # Given
    user = FFAdminUser.objects.create(email="test@example.com")
    organisation = Organisation.objects.create(name="Test org")
    Subscription.objects.filter(organisation=organisation).update(
        subscription_id=subscription_id
    )
    user.add_organisation(organisation)

    settings.PIPEDRIVE_LEAD_LABEL_EXISTING_CUSTOMER_ID = label_id

    # When
    label_ids = PipedriveLeadTracker.get_label_ids_for_user(user)

    # Then
    assert label_ids == expected_label_ids
