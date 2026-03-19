import json
import typing
import uuid
from datetime import timedelta

import pytest
from chargebee import APIError as ChargebeeAPIError  # type: ignore[import-untyped]
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.utils import timezone
from pytest_django.fixtures import SettingsWrapper
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]
from pytest_mock.plugin import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from organisations.invites.models import Invite, InviteLink
from organisations.models import Organisation, OrganisationRole, Subscription
from users.models import FFAdminUser, UserPermissionGroup


def test_create_invite_link__with_expiry_date__returns_created(
    organisation: Organisation,
    admin_client: APIClient,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:organisation-invite-links-list",
        args=[organisation.pk],
    )
    tomorrow = timezone.now() + timedelta(days=1)
    expires_at = tomorrow.strftime("%Y-%m-%dT%H:%M:%SZ")
    data = {"expires_at": expires_at}

    # When
    response = admin_client.post(url, data=data)

    # Then
    assert response.status_code == status.HTTP_201_CREATED

    assert response.data["hash"]
    assert response.data["id"]
    assert response.data["expires_at"] == expires_at
    assert response.data["role"] == "USER"


def test_get_invite_links__multiple_roles_exist__returns_all_links(
    organisation: Organisation,
    admin_client: APIClient,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:organisation-invite-links-list",
        args=[organisation.pk],
    )
    for role in OrganisationRole:
        InviteLink.objects.create(organisation=organisation, role=role.name)

    # update subscription to add another seat
    organisation.subscription.max_seats = 3
    organisation.subscription.save()

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert len(response.data) == 2
    expected_attributes = ("hash", "id", "expires_at")
    for invite_link in response.data:
        assert all(attr in invite_link for attr in expected_attributes)


def test_get_invite_links__seats_exceeded__returns_400(
    settings: SettingsWrapper,
    organisation: Organisation,
    admin_client: APIClient,
) -> None:
    # Given
    settings.ENABLE_CHARGEBEE = True
    url = reverse(
        "api-v1:organisations:organisation-invite-links-list",
        args=[organisation.pk],
    )

    for role in OrganisationRole:
        InviteLink.objects.create(organisation=organisation, role=role.name)

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_delete_invite_link__valid_invite__returns_204(
    settings: SettingsWrapper,
    organisation: Organisation,
    admin_client: APIClient,
) -> None:
    # Given
    settings.ENABLE_CHARGEBEE = True
    invite = InviteLink.objects.create(organisation=organisation)
    url = reverse(
        "api-v1:organisations:organisation-invite-links-detail",
        args=[organisation.pk, invite.pk],
    )

    # update subscription to add another seat
    organisation.subscription.max_seats = 3
    organisation.subscription.save()

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_invite_link__seats_exceeded__returns_400(
    organisation: Organisation,
    admin_client: APIClient,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.ENABLE_CHARGEBEE = True
    invite = InviteLink.objects.create(organisation=organisation)
    url = reverse(
        "api-v1:organisations:organisation-invite-links-detail",
        args=[organisation.pk, invite.pk],
    )

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_update_invite_link__patch_request__returns_405(  # type: ignore[no-untyped-def]
    invite_link, admin_client, organisation
):
    # Given
    url = reverse(
        "api-v1:organisations:organisation-invite-links-detail",
        args=[organisation.pk, invite_link.pk],
    )
    tomorrow = timezone.now() + timedelta(days=1)
    data = {"expires_at": tomorrow.isoformat()}

    # When
    response = admin_client.patch(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_join_organisation__invite_with_permission_groups__adds_user_to_groups(
    organisation: Organisation,
    user_permission_group: UserPermissionGroup,
    enterprise_subscription: Subscription,
    api_client: APIClient,
) -> None:
    # Given
    new_user = FFAdminUser.objects.create(
        email=f"example{uuid.uuid4()}@example.com",
    )
    api_client.force_authenticate(user=new_user)

    invite = Invite.objects.create(email=new_user.email, organisation=organisation)
    invite.permission_groups.add(user_permission_group)

    # update subscription to add another seat
    current_seats = organisation.users.count()
    enterprise_subscription.max_seats = current_seats + 1
    enterprise_subscription.save()

    url = reverse("api-v1:users:user-join-organisation", args=[invite.hash])
    data = {"hubspotutk": "somehubspotdata"}

    # When
    response = api_client.post(url, data)
    new_user.refresh_from_db()

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert organisation in new_user.organisations.all()
    assert user_permission_group in new_user.permission_groups.all()
    # and invite is deleted
    with pytest.raises(Invite.DoesNotExist):
        invite.refresh_from_db()


@pytest.mark.saas_mode
def test_create_invite__with_permission_groups__returns_created(
    admin_client: APIClient,
    organisation: Organisation,
    user_permission_group: UserPermissionGroup,
    admin_user: FFAdminUser,
    chargebee_subscription: Subscription,
) -> None:
    # Given
    # update subscription to add another seat
    chargebee_subscription.max_seats = 2
    chargebee_subscription.save()

    url = reverse(
        "api-v1:organisations:organisation-invites-list",
        args=[organisation.pk],
    )
    email = "test@example.com"
    data = {"email": email, "permission_groups": [user_permission_group.id]}

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    assert response.status_code == status.HTTP_201_CREATED, response.json()
    # and
    invite = Invite.objects.get(email=email)
    assert invite.permission_groups.first() == user_permission_group
    assert invite.invited_by == admin_user


@pytest.mark.saas_mode
def test_create_invite__permission_group_from_another_org__returns_400(
    admin_client: APIClient,
    organisation: Organisation,
    chargebee_subscription: Subscription,
) -> None:
    # Given
    # update subscription to add another seat
    chargebee_subscription.max_seats = 2
    chargebee_subscription.save()

    another_organisation = Organisation.objects.create(name="Another Organisation")
    user_permission_group = UserPermissionGroup.objects.create(
        organisation=another_organisation, name="Group"
    )

    url = reverse(
        "api-v1:organisations:organisation-invites-list",
        args=[organisation.pk],
    )
    email = "test@example.com"
    data = {"email": email, "permission_groups": [user_permission_group.id]}

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response_json = response.json()
    assert response_json == {
        "permission_groups": [
            f'Invalid pk "{user_permission_group.pk}" - object does not exist.'
        ]
    }


def test_create_invite__seats_exceeded__returns_400(
    admin_client: APIClient,
    organisation: Organisation,
    user_permission_group: UserPermissionGroup,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:organisation-invites-list",
        args=[organisation.pk],
    )
    email = "test@example.com"
    data = {"email": email, "permission_groups": [user_permission_group.id]}

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["detail"]
        == "Please upgrade your plan to add additional seats/users"
    )


def test_retrieve_invite__valid_invite__returns_200(  # type: ignore[no-untyped-def]
    admin_client, organisation, user_permission_group, invite
):
    # Given
    url = reverse(
        "api-v1:organisations:organisation-invites-detail",
        args=[organisation.id, invite.id],
    )
    # When
    response = admin_client.get(url)
    # Then
    assert response.status_code == status.HTTP_200_OK


def test_delete_invite__valid_invite__returns_204(  # type: ignore[no-untyped-def]
    admin_client, organisation, user_permission_group, invite
):
    # Given
    url = reverse(
        "api-v1:organisations:organisation-invites-detail",
        args=[organisation.id, invite.id],
    )
    # When
    response = admin_client.delete(url)
    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_update_invite__put_request__returns_405(  # type: ignore[no-untyped-def]
    admin_client, organisation, user_permission_group, invite
):
    # Given
    url = reverse(
        "api-v1:organisations:organisation-invites-detail",
        args=[organisation.id, invite.id],
    )
    data = {"email": "new_email@example.com"}

    # When
    response = admin_client.put(url, data=data)

    # Then
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.saas_mode
@pytest.mark.parametrize(
    "invite_object, url",
    [
        (lazy_fixture("invite"), "api-v1:users:user-join-organisation"),
        (lazy_fixture("invite_link"), "api-v1:users:user-join-organisation-link"),
    ],
)
def test_join_organisation__exceeds_plan_limit_saas__returns_400(
    staff_client: APIClient,
    invite_object: Invite | InviteLink,
    url: str,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.ENABLE_CHARGEBEE = True
    url = reverse(url, args=[invite_object.hash])
    # When
    response = staff_client.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["detail"]
        == "Please upgrade your plan to add additional seats/users"
    )


@pytest.mark.enterprise_mode
@pytest.mark.parametrize(
    "invite_object, url",
    [
        (lazy_fixture("invite"), "api-v1:users:user-join-organisation"),
        (lazy_fixture("invite_link"), "api-v1:users:user-join-organisation-link"),
    ],
)
def test_join_organisation__exceeds_plan_limit_self_hosted__returns_400(
    staff_client: APIClient,
    invite_object: Invite | InviteLink,
    url: str,
    organisation: Organisation,
    enterprise_subscription: Subscription,
) -> None:
    # Given
    url = reverse(url, args=[invite_object.hash])

    enterprise_subscription.max_seats = 1
    enterprise_subscription.save()

    # When
    response = staff_client.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["detail"]
        == "Please upgrade your plan to add additional seats/users"
    )


@pytest.mark.saas_mode
@pytest.mark.parametrize(
    "invite_object, url",
    [
        (lazy_fixture("invite"), "api-v1:users:user-join-organisation"),
        (lazy_fixture("invite_link"), "api-v1:users:user-join-organisation-link"),
    ],
)
def test_join_organisation__payment_fails__returns_400(
    staff_client: APIClient,
    invite_object: Invite | InviteLink,
    url: str,
    subscription: Subscription,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.ENABLE_CHARGEBEE = True

    url = reverse(url, args=[invite_object.hash])

    subscription.plan = "scale-up"
    subscription.subscription_id = "chargemepls"
    subscription.save()

    mocked_cb_subscription = mocker.MagicMock(addons=[])

    mocked_chargebee = mocker.patch(
        "organisations.chargebee.chargebee.chargebee_client", autospec=True
    )
    mocked_chargebee.Subscription.retrieve.return_value = mocked_cb_subscription

    chargebee_response_data = {
        "message": "Subscription cannot be created as the payment collection failed. Gateway Error: Card declined.",
        "type": "payment",
        "api_error_code": "payment_processing_failed",
        "param": "item_id",
        "error_code": "DeprecatedField",
    }

    mocked_chargebee.Subscription.update.side_effect = ChargebeeAPIError(
        http_code=400, json_obj=chargebee_response_data
    )

    # When
    response = staff_client.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["detail"]
        == "Joining the organisation has failed due to a payment issue. Please contact your organisation's admin."
    )


def test_join_organisation_from_link__invite_links_disabled__returns_403(
    organisation: Organisation,
    invite_link: InviteLink,
    settings: SettingsWrapper,
    django_user_model: typing.Type[AbstractUser],
    api_client: APIClient,
) -> None:
    # Given
    settings.DISABLE_INVITE_LINKS = True
    url = reverse("api-v1:users:user-join-organisation-link", args=[invite_link.hash])

    new_user = FFAdminUser.objects.create(email=f"user{uuid.uuid4()}@example.com")
    api_client.force_authenticate(user=new_user)

    # When
    response = api_client.post(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
