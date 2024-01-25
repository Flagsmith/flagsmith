import json
import typing
from datetime import timedelta

import pytest
from chargebee import APIError as ChargebeeAPIError
from django.urls import reverse
from django.utils import timezone
from pytest_django.fixtures import SettingsWrapper
from pytest_lazyfixture import lazy_fixture
from pytest_mock.plugin import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from organisations.invites.models import Invite, InviteLink
from organisations.models import Organisation, OrganisationRole, Subscription
from users.models import FFAdminUser


def test_create_invite_link(
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


def test_get_invite_links_for_organisation(
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


def test_get_invite_links_for_organisation_returns_400_if_seats_are_over(
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


def test_delete_invite_link_for_organisation(
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


def test_delete_invite_link_for_organisation_return_400_if_seats_are_over(
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


def test_update_invite_link_returns_405(invite_link, admin_client, organisation):
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


def test_join_organisation_with_permission_groups(
    test_user, test_user_client, organisation, user_permission_group, subscription
):
    # Given
    invite = Invite.objects.create(email=test_user.email, organisation=organisation)
    invite.permission_groups.add(user_permission_group)

    # update subscription to add another seat
    subscription.max_seats = 2
    subscription.save()

    url = reverse("api-v1:users:user-join-organisation", args=[invite.hash])

    # When
    response = test_user_client.post(url)
    test_user.refresh_from_db()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert organisation in test_user.organisations.all()
    assert user_permission_group in test_user.permission_groups.all()
    # and invite is deleted
    with pytest.raises(Invite.DoesNotExist):
        invite.refresh_from_db()


def test_create_invite_with_permission_groups(
    admin_client, organisation, user_permission_group, admin_user, subscription
):
    # Given
    # update subscription to add another seat
    subscription.max_seats = 2
    subscription.save()

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
    assert response.status_code == status.HTTP_201_CREATED
    # and
    invite = Invite.objects.get(email=email)
    assert invite.permission_groups.first() == user_permission_group
    assert invite.invited_by == admin_user


def test_create_invite_returns_400_if_seats_are_over(
    admin_client,
    organisation,
    user_permission_group,
    admin_user,
    subscription,
    settings,
):
    # Given
    settings.AUTO_SEAT_UPGRADE_PLANS = ["scale-up"]
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
        == "Please Upgrade your plan to add additional seats/users"
    )


def test_retrieve_invite(admin_client, organisation, user_permission_group, invite):
    # Given
    url = reverse(
        "api-v1:organisations:organisation-invites-detail",
        args=[organisation.id, invite.id],
    )
    # When
    response = admin_client.get(url)
    # Then
    assert response.status_code == status.HTTP_200_OK


def test_delete_invite(admin_client, organisation, user_permission_group, invite):
    # Given
    url = reverse(
        "api-v1:organisations:organisation-invites-detail",
        args=[organisation.id, invite.id],
    )
    # When
    response = admin_client.delete(url)
    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_update_invite_returns_405(
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


@pytest.mark.parametrize(
    "invite_object, url",
    [
        (lazy_fixture("invite"), "api-v1:users:user-join-organisation"),
        (lazy_fixture("invite_link"), "api-v1:users:user-join-organisation-link"),
    ],
)
def test_join_organisation_returns_400_if_exceeds_plan_limit(
    test_user_client,
    organisation,
    admin_user,
    invite_object,
    url,
    subscription,
    settings,
):
    # Given
    settings.ENABLE_CHARGEBEE = True
    settings.AUTO_SEAT_UPGRADE_PLANS = ["scale-up"]
    url = reverse(url, args=[invite_object.hash])
    # When
    response = test_user_client.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["detail"]
        == "Please Upgrade your plan to add additional seats/users"
    )


@pytest.mark.parametrize(
    "invite_object, url",
    [
        (lazy_fixture("invite"), "api-v1:users:user-join-organisation"),
        (lazy_fixture("invite_link"), "api-v1:users:user-join-organisation-link"),
    ],
)
def test_join_organisation_returns_400_if_payment_fails(
    test_user_client: APIClient,
    organisation: Organisation,
    admin_user: FFAdminUser,
    invite_object: typing.Union[Invite, InviteLink],
    url: str,
    subscription: Subscription,
    settings: SettingsWrapper,
    mocker: MockerFixture,
):
    # Given
    settings.ENABLE_CHARGEBEE = True
    settings.AUTO_SEAT_UPGRADE_PLANS = ["scale-up"]

    url = reverse(url, args=[invite_object.hash])

    subscription.plan = "scale-up"
    subscription.subscription_id = "chargemepls"
    subscription.save()

    mocked_cb_subscription = mocker.MagicMock(addons=[])

    mocked_chargebee = mocker.patch("organisations.chargebee.chargebee.chargebee")
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
    response = test_user_client.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["detail"]
        == "Joining the organisation has failed due to a payment issue. Please contact your organisation's admin."
    )


def test_join_organisation_from_link_returns_403_if_invite_links_disabled(
    test_user_client, organisation, invite_link, settings
):
    # Given
    settings.DISABLE_INVITE_LINKS = True
    url = reverse("api-v1:users:user-join-organisation-link", args=[invite_link.hash])

    # When
    response = test_user_client.post(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
