import json
import typing

import pytest
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from djoser import utils
from djoser.email import PasswordResetEmail
from pytest_django import DjangoAssertNumQueries
from rest_framework import status
from rest_framework.test import APIClient

from organisations.invites.models import Invite, InviteLink
from organisations.models import Organisation, OrganisationRole
from users.models import FFAdminUser, UserPermissionGroup


def test_join_organisation(
    staff_user: FFAdminUser,
    staff_client: APIClient,
) -> None:
    # Given
    organisation = Organisation.objects.create(name="test org")
    invite = Invite.objects.create(email=staff_user.email, organisation=organisation)
    url = reverse("api-v1:users:user-join-organisation", args=[invite.hash])

    # When
    response = staff_client.post(url)
    staff_user.refresh_from_db()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert organisation in staff_user.organisations.all()


def test_join_organisation_via_link(
    staff_user: FFAdminUser,
    staff_client: APIClient,
) -> None:
    # Given
    organisation = Organisation.objects.create(name="test org")
    invite = InviteLink.objects.create(organisation=organisation)
    url = reverse("api-v1:users:user-join-organisation-link", args=[invite.hash])

    # When
    response = staff_client.post(url)
    staff_user.refresh_from_db()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert organisation in staff_user.organisations.all()


def test_cannot_join_organisation_via_expired_link(
    staff_user: FFAdminUser,
    staff_client: APIClient,
) -> None:
    # Given
    organisation = Organisation.objects.create(name="test org")
    invite = InviteLink.objects.create(
        organisation=organisation,
        expires_at=timezone.now() - relativedelta(days=2),
    )
    url = reverse("api-v1:users:user-join-organisation-link", args=[invite.hash])

    # When
    response = staff_client.post(url)
    staff_user.refresh_from_db()

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert organisation not in staff_user.organisations.all()


def test_user_can_join_second_organisation(
    organisation: Organisation,
    staff_user: FFAdminUser,
    staff_client: APIClient,
):
    # Given
    new_organisation = Organisation.objects.create(name="New org")
    invite = Invite.objects.create(
        email=staff_user.email, organisation=new_organisation
    )
    url = reverse("api-v1:users:user-join-organisation", args=[invite.hash])

    # When
    response = staff_client.post(url)
    staff_user.refresh_from_db()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert (
        new_organisation in staff_user.organisations.all()
        and organisation in staff_user.organisations.all()
    )


def test_cannot_join_organisation_with_different_email_address_than_invite(
    staff_user: FFAdminUser,
    staff_client: APIClient,
) -> None:
    # Given
    organisation = Organisation.objects.create(name="test org")
    invite = Invite.objects.create(
        email="some-other-email@test.com", organisation=organisation
    )
    url = reverse("api-v1:users:user-join-organisation", args=[invite.hash])

    # When
    response = staff_client.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert organisation not in staff_user.organisations.all()


def test_can_join_organisation_as_admin_if_invite_role_is_admin(
    staff_user: FFAdminUser,
    staff_client: APIClient,
) -> None:
    # Given
    organisation = Organisation.objects.create(name="test org")
    invite = Invite.objects.create(
        email=staff_user.email,
        organisation=organisation,
        role=OrganisationRole.ADMIN.name,
    )
    url = reverse("api-v1:users:user-join-organisation", args=[invite.hash])

    # When
    staff_client.post(url)

    # Then
    assert staff_user.is_organisation_admin(organisation)


def test_admin_can_update_role_for_a_user_in_organisation(
    admin_user: FFAdminUser,
    admin_client: APIClient,
    organisation: Organisation,
):
    # Given
    organisation_user = FFAdminUser.objects.create(email="org_user@org.com")
    organisation_user.add_organisation(organisation)
    url = reverse(
        "api-v1:organisations:organisation-users-update-role",
        args=[organisation.pk, organisation_user.pk],
    )
    data = {"role": OrganisationRole.ADMIN.name}

    # When
    response = admin_client.post(url, data=data)

    # Then
    assert response.status_code == status.HTTP_200_OK

    # and
    assert (
        organisation_user.get_organisation_role(organisation)
        == OrganisationRole.ADMIN.name
    )


def test_admin_can_get_users_in_organisation(
    admin_user: FFAdminUser,
    admin_client: APIClient,
    staff_user: FFAdminUser,
    organisation: Organisation,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    # Given
    organisation_user = FFAdminUser.objects.create(email="org_user@org.com")
    organisation_user.add_organisation(organisation)
    url = reverse(
        "api-v1:organisations:organisation-users-list", args=[organisation.pk]
    )

    # add some more users to test for N+1 issues
    additional_user1 = FFAdminUser.objects.create(email="additional_user_1@org.com")
    additional_user1.add_organisation(organisation)
    additional_user2 = FFAdminUser.objects.create(email="additional_user_2@org.com")
    additional_user2.add_organisation(organisation)

    # When
    with django_assert_num_queries(5):
        response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.data[0]["email"] == admin_user.email
    assert response.data[1]["email"] == staff_user.email
    assert response.data[2]["email"] == organisation_user.email
    assert response.data[3]["email"] == additional_user1.email
    assert response.data[4]["email"] == additional_user2.email


def test_org_user_can_get_users_in_organisation(
    staff_user: FFAdminUser,
    staff_client: APIClient,
    organisation: Organisation,
    admin_user: FFAdminUser,
) -> None:
    # Given
    organisation_user = FFAdminUser.objects.create(email="org_user@org.com")
    organisation_user.add_organisation(organisation)
    url = reverse(
        "api-v1:organisations:organisation-users-list", args=[organisation.pk]
    )

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.data[0]["email"] == staff_user.email
    assert response.data[1]["email"] == admin_user.email
    assert response.data[2]["email"] == organisation_user.email


def test_org_user_can_exclude_themself_when_getting_users_in_organisation(
    staff_client: APIClient,
    staff_user: FFAdminUser,
    organisation: Organisation,
    admin_user: FFAdminUser,
):
    # Given
    organisation_user = FFAdminUser.objects.create(email="org_user@org.com")
    organisation_user.add_organisation(organisation)
    base_url = reverse(
        "api-v1:organisations:organisation-users-list", args=[organisation.pk]
    )
    url = f"{base_url}?exclude_current=true"

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2
    assert response.data[0]["id"] == admin_user.id
    assert response.data[1]["id"] == organisation_user.id


def test_organisation_admin_can_interact_with_groups(
    organisation: Organisation,
    admin_client: APIClient,
) -> None:
    # Given
    # Create a group
    create_data = {"name": "Test Group"}
    url = reverse(
        "api-v1:organisations:organisation-groups-list", args=[organisation.id]
    )

    # When / Then
    response = admin_client.post(url, data=create_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert UserPermissionGroup.objects.filter(name=create_data["name"]).exists()
    group_id = response.json()["id"]

    # Group appears in the groups list
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"][0]["name"] == "Test Group"

    # Update the group
    update_data = {"name": "New Group Name"}
    url = reverse(
        "api-v1:organisations:organisation-groups-detail",
        args=[organisation.id, group_id],
    )

    response = admin_client.patch(url, data=update_data)
    assert response.status_code == status.HTTP_200_OK

    # Update is reflected when getting the group
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == update_data["name"]

    # Delete the group
    response = admin_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not UserPermissionGroup.objects.filter(name=update_data["name"]).exists()


def test_staff_user_cannot_post_to_groups(
    staff_client: APIClient,
    organisation: Organisation,
) -> None:
    group_name = "Test Group"
    UserPermissionGroup.objects.create(name=group_name, organisation=organisation)
    data = {"name": "New Test Group"}

    url = reverse(
        "api-v1:organisations:organisation-groups-list", args=[organisation.id]
    )
    response = staff_client.post(url, data=data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_staff_user_cannot_put_to_groups(
    staff_client: APIClient,
    organisation: Organisation,
) -> None:
    group_name = "Test Group"
    group = UserPermissionGroup.objects.create(
        name=group_name, organisation=organisation
    )
    url = reverse(
        "api-v1:organisations:organisation-groups-detail",
        args=[organisation.id, group.id],
    )

    response = staff_client.put(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_staff_user_cannot_get_to_groups(
    staff_client: APIClient,
    organisation: Organisation,
) -> None:
    group_name = "Test Group"
    group = UserPermissionGroup.objects.create(
        name=group_name, organisation=organisation
    )
    url = reverse(
        "api-v1:organisations:organisation-groups-detail",
        args=[organisation.id, group.id],
    )

    response = staff_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_staff_user_cannot_delete_to_groups(
    staff_client: APIClient,
    organisation: Organisation,
) -> None:
    group_name = "Test Group"
    group = UserPermissionGroup.objects.create(
        name=group_name, organisation=organisation
    )
    url = reverse(
        "api-v1:organisations:organisation-groups-detail",
        args=[organisation.id, group.id],
    )

    response = staff_client.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert UserPermissionGroup.objects.filter(name=group_name).exists()


def test_can_add_multiple_users_including_current_user(
    staff_user: FFAdminUser,
    organisation: Organisation,
    admin_user: FFAdminUser,
    admin_client: APIClient,
) -> None:
    # Given
    group = UserPermissionGroup.objects.create(
        name="Test Group", organisation=organisation
    )
    url = reverse(
        "api-v1:organisations:organisation-groups-add-users",
        args=[organisation.id, group.id],
    )
    data = {"user_ids": [admin_user.id, staff_user.id]}

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert all(user in group.users.all() for user in [admin_user, staff_user])


def test_cannot_add_user_from_another_organisation(
    admin_client: APIClient,
    organisation: Organisation,
):
    # Given
    another_organisation = Organisation.objects.create(name="Another organisation")
    another_user = FFAdminUser.objects.create(email="anotheruser@anotherorg.com")
    another_user.add_organisation(another_organisation, role=OrganisationRole.USER)
    group = UserPermissionGroup.objects.create(
        name="Test Group", organisation=organisation
    )
    url = reverse(
        "api-v1:organisations:organisation-groups-add-users",
        args=[organisation.id, group.id],
    )
    data = {"user_ids": [another_user.id]}

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_cannot_add_same_user_twice(
    staff_user: FFAdminUser,
    organisation: Organisation,
    admin_client: APIClient,
) -> None:
    # Given
    group = UserPermissionGroup.objects.create(
        name="Test Group", organisation=organisation
    )
    group.users.add(staff_user)
    url = reverse(
        "api-v1:organisations:organisation-groups-add-users",
        args=[organisation.id, group.id],
    )
    data = {"user_ids": [staff_user.id]}

    # When
    admin_client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert staff_user in group.users.all() and group.users.count() == 1


def test_remove_users_from_group(
    staff_user: FFAdminUser,
    organisation: Organisation,
    admin_user: FFAdminUser,
    admin_client: APIClient,
) -> None:
    # Given
    group = UserPermissionGroup.objects.create(
        name="Test Group", organisation=organisation
    )
    group.users.add(staff_user, admin_user)
    url = reverse(
        "api-v1:organisations:organisation-groups-remove-users",
        args=[organisation.id, group.id],
    )

    data = {"user_ids": [staff_user.id]}

    # When
    admin_client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    # staff user has been removed
    assert staff_user not in group.users.all()

    # but admin user still remains
    assert admin_user in group.users.all()


def test_remove_users_silently_fails_if_user_not_in_group(
    staff_user: FFAdminUser,
    organisation: Organisation,
    admin_client: APIClient,
    admin_user: FFAdminUser,
) -> None:
    # Given
    group = UserPermissionGroup.objects.create(
        name="Test Group", organisation=organisation
    )
    group.users.add(admin_user)
    url = reverse(
        "api-v1:organisations:organisation-groups-remove-users",
        args=[organisation.id, group.id],
    )
    data = {"user_ids": [staff_user.id]}

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    # request was successful
    assert response.status_code == status.HTTP_200_OK
    # and admin user is still in the group
    assert admin_user in group.users.all()


def test_user_permission_group_can_update_is_default(
    admin_client, organisation, user_permission_group
):
    # Given
    args = [organisation.id, user_permission_group.id]
    url = reverse("api-v1:organisations:organisation-groups-detail", args=args)

    data = {"is_default": True, "name": user_permission_group.name}

    # When
    response = admin_client.put(url, data=data)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["is_default"] is True

    # and
    user_permission_group.refresh_from_db()
    assert user_permission_group.is_default is True


def test_user_permission_group_can_update_external_id(
    admin_client, organisation, user_permission_group
):
    # Given
    args = [organisation.id, user_permission_group.id]
    url = reverse("api-v1:organisations:organisation-groups-detail", args=args)
    external_id = "some_external_id"

    data = {"external_id": external_id, "name": user_permission_group.name}

    # When
    response = admin_client.put(url, data=data)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["external_id"] == external_id


def test_users_in_organisation_have_last_login(
    admin_client, organisation, rf, mocker, admin_user
):
    # Given
    req = rf.get("/")
    req.session = mocker.MagicMock()

    # let's log the user in to generate `last_login`
    login(req, admin_user, backend="django.contrib.auth.backends.ModelBackend")
    url = reverse(
        "api-v1:organisations:organisation-users-list", args=[organisation.id]
    )

    # When
    res = admin_client.get(url)

    # Then
    assert res.json()[0]["last_login"] is not None
    assert res.status_code == status.HTTP_200_OK


def test_retrieve_user_permission_group_includes_group_admin(
    admin_client, admin_user, organisation, user_permission_group
):
    # Given
    group_admin_user = FFAdminUser.objects.create(email="groupadminuser@example.com")
    group_admin_user.permission_groups.add(user_permission_group)
    group_admin_user.make_group_admin(user_permission_group.id)

    url = reverse(
        "api-v1:organisations:organisation-groups-detail",
        args=[organisation.id, user_permission_group.id],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()

    users = response_json["users"]

    assert (
        next(filter(lambda u: u["id"] == admin_user.id, users))["group_admin"] is False
    )
    assert (
        next(filter(lambda u: u["id"] == group_admin_user.id, users))["group_admin"]
        is True
    )


def test_group_admin_can_retrieve_group(
    organisation: Organisation,
    django_user_model: typing.Type[AbstractUser],
    api_client: APIClient,
):
    # Given
    user = django_user_model.objects.create(email="test@example.com")
    user.add_organisation(organisation)
    group = UserPermissionGroup.objects.create(
        organisation=organisation, name="Test group"
    )
    user.add_to_group(group, group_admin=True)

    api_client.force_authenticate(user)
    url = reverse(
        "api-v1:organisations:organisation-groups-detail",
        args=[organisation.id, group.id],
    )

    # When
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_delete_user():
    def delete_user(
        user: FFAdminUser, password: str, delete_orphan_organisations: bool = True
    ):
        client = APIClient()
        client.force_authenticate(user)
        data = {
            "current_password": password,
            "delete_orphan_organisations": delete_orphan_organisations,
        }
        url = "/api/v1/auth/users/me/"
        return client.delete(
            url, data=json.dumps(data), content_type="application/json"
        )

    # create a couple of users
    email1 = "test1@example.com"
    email2 = "test2@example.com"
    email3 = "test3@example.com"
    password = "password"
    user1 = FFAdminUser.objects.create_user(email=email1, password=password)
    user2 = FFAdminUser.objects.create_user(email=email2, password=password)
    user3 = FFAdminUser.objects.create_user(email=email3, password=password)

    # crete some organizations
    org1 = Organisation.objects.create(name="org1")
    org2 = Organisation.objects.create(name="org2")
    org3 = Organisation.objects.create(name="org3")

    # add the test user 1 to all the organizations
    org1.users.add(user1)
    org2.users.add(user1)
    org3.users.add(user1)

    # add test user 2 to org2 and user 3 to to org1
    org2.users.add(user2)
    org1.users.add(user3)

    # Configuration: org1: [user1, user3], org2: [user1, user2], org3: [user1]

    # Delete user2
    response = delete_user(user2, password)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not FFAdminUser.objects.filter(email=email2).exists()

    # All organisations remain since user 2 has org2 as only organization and it has 2 users
    assert Organisation.objects.filter(name="org3").count() == 1
    assert Organisation.objects.filter(name="org1").count() == 1
    assert Organisation.objects.filter(name="org2").count() == 1

    # Delete user1
    response = delete_user(user1, password)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not FFAdminUser.objects.filter(email=email1).exists()

    # organization org3 and org2 are deleted since its only user is user1
    assert Organisation.objects.filter(name="org3").count() == 0
    assert Organisation.objects.filter(name="org2").count() == 0

    # org1 remain
    assert Organisation.objects.filter(name="org1").count() == 1

    # user3 remain
    assert FFAdminUser.objects.filter(email=email3).exists()

    # Delete user3
    response = delete_user(user3, password, False)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not FFAdminUser.objects.filter(email=email3).exists()
    assert Organisation.objects.filter(name="org1").count() == 1


@pytest.mark.django_db
def test_change_email_address_api(mocker):
    # Given
    mocked_task = mocker.patch("users.signals.send_email_changed_notification_email")
    # create an user
    old_email = "test_user@test.com"
    first_name = "firstname"
    user = FFAdminUser.objects.create_user(
        username="test_user",
        email=old_email,
        first_name=first_name,
        last_name="user",
        password="password",
    )

    client = APIClient()
    client.force_authenticate(user)
    new_email = "test_user1@test.com"
    data = {"new_email": new_email, "current_password": "password"}

    url = reverse("api-v1:custom_auth:ffadminuser-set-username")

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert user.email == new_email

    args, kwargs = mocked_task.delay.call_args

    assert len(args) == 0
    assert len(kwargs) == 1
    assert kwargs["args"] == (first_name, settings.DEFAULT_FROM_EMAIL, old_email)


@pytest.mark.django_db
def test_send_reset_password_emails_rate_limit(settings, client, test_user):
    # Given
    settings.MAX_PASSWORD_RESET_EMAILS = 2
    settings.PASSWORD_RESET_EMAIL_COOLDOWN = 60

    url = reverse("api-v1:custom_auth:ffadminuser-reset-password")
    data = {"email": test_user.email}

    # When
    for _ in range(5):
        response = client.post(
            url, data=json.dumps(data), content_type="application/json"
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    # Then - we should only have two emails
    assert len(mail.outbox) == 2
    isinstance(mail.outbox[0], PasswordResetEmail)
    isinstance(mail.outbox[1], PasswordResetEmail)

    # clear the outbox
    mail.outbox.clear()

    # Next, let's reduce the cooldown to 1 second and try again
    settings.PASSWORD_RESET_EMAIL_COOLDOWN = 0.001
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then - we should receive another email
    assert response.status_code == status.HTTP_204_NO_CONTENT

    assert len(mail.outbox) == 1
    isinstance(mail.outbox[0], PasswordResetEmail)


@pytest.mark.django_db
def test_send_reset_password_emails_rate_limit_resets_after_password_reset(
    settings, client, test_user
):
    # Given
    settings.MAX_PASSWORD_RESET_EMAILS = 2
    settings.PASSWORD_RESET_EMAIL_COOLDOWN = 60 * 60 * 24

    url = reverse("api-v1:custom_auth:ffadminuser-reset-password")
    data = {"email": test_user.email}

    # First, let's hit the limit of emails we can send
    for _ in range(5):
        response = client.post(
            url, data=json.dumps(data), content_type="application/json"
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    # Then - we should only have two emails
    assert len(mail.outbox) == 2
    mail.outbox.clear()

    # Next, let's reset the password
    reset_password_data = {
        "new_password": "new_password",
        "re_new_password": "new_password",
        "uid": utils.encode_uid(test_user.pk),
        "token": default_token_generator.make_token(test_user),
    }
    reset_password_confirm_url = reverse(
        "api-v1:custom_auth:ffadminuser-reset-password-confirm"
    )
    response = client.post(
        reset_password_confirm_url,
        data=json.dumps(reset_password_data),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Finally, let's try to send another email
    client.post(url, data=json.dumps(data), content_type="application/json")

    # Then - we should receive another email
    assert len(mail.outbox) == 1
