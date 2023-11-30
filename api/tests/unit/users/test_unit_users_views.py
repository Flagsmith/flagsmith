import json
import typing

import pytest
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from djoser import utils
from djoser.email import PasswordResetEmail
from rest_framework import status
from rest_framework.test import APIClient

from organisations.invites.models import Invite, InviteLink
from organisations.models import Organisation, OrganisationRole
from users.models import FFAdminUser, UserPermissionGroup
from util.tests import Helper


@pytest.mark.django_db
class UserTestCase(TestCase):
    auth_base_url = "/api/v1/auth/"
    register_template = (
        "{ "
        '"email": "%s", '
        '"first_name": "%s", '
        '"last_name": "%s", '
        '"password1": "%s", '
        '"password2": "%s" '
        "}"
    )
    login_template = "{" '"email": "%s",' '"password": "%s"' "}"

    def setUp(self):
        self.client = APIClient()
        self.user = Helper.create_ffadminuser()
        self.client.force_authenticate(user=self.user)

        self.organisation = Organisation.objects.create(name="test org")

    def tearDown(self) -> None:
        Helper.clean_up()

    def test_join_organisation(self):
        # Given
        invite = Invite.objects.create(
            email=self.user.email, organisation=self.organisation
        )
        url = reverse("api-v1:users:user-join-organisation", args=[invite.hash])

        # When
        response = self.client.post(url)
        self.user.refresh_from_db()

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert self.organisation in self.user.organisations.all()

    def test_join_organisation_via_link(self):
        # Given
        invite = InviteLink.objects.create(organisation=self.organisation)
        url = reverse("api-v1:users:user-join-organisation-link", args=[invite.hash])

        # When
        response = self.client.post(url)
        self.user.refresh_from_db()

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert self.organisation in self.user.organisations.all()

    def test_cannot_join_organisation_via_expired_link(self):
        # Given
        invite = InviteLink.objects.create(
            organisation=self.organisation,
            expires_at=timezone.now() - relativedelta(days=2),
        )
        url = reverse("api-v1:users:user-join-organisation-link", args=[invite.hash])

        # When
        response = self.client.post(url)

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert self.organisation not in self.user.organisations.all()

    def test_user_can_join_second_organisation(self):
        # Given
        self.user.add_organisation(self.organisation)
        new_organisation = Organisation.objects.create(name="New org")
        invite = Invite.objects.create(
            email=self.user.email, organisation=new_organisation
        )
        url = reverse("api-v1:users:user-join-organisation", args=[invite.hash])

        # When
        response = self.client.post(url)
        self.user.refresh_from_db()

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert (
            new_organisation in self.user.organisations.all()
            and self.organisation in self.user.organisations.all()
        )

    def test_cannot_join_organisation_with_different_email_address_than_invite(self):
        # Given
        invite = Invite.objects.create(
            email="some-other-email@test.com", organisation=self.organisation
        )
        url = reverse("api-v1:users:user-join-organisation", args=[invite.hash])

        # When
        res = self.client.post(url)

        # Then
        assert res.status_code == status.HTTP_400_BAD_REQUEST

        # and
        assert self.organisation not in self.user.organisations.all()

    def test_can_join_organisation_as_admin_if_invite_role_is_admin(self):
        # Given
        invite = Invite.objects.create(
            email=self.user.email,
            organisation=self.organisation,
            role=OrganisationRole.ADMIN.name,
        )
        url = reverse("api-v1:users:user-join-organisation", args=[invite.hash])

        # When
        self.client.post(url)

        # Then
        assert self.user.is_organisation_admin(self.organisation)

    def test_admin_can_update_role_for_a_user_in_organisation(self):
        # Given
        self.user.add_organisation(self.organisation, OrganisationRole.ADMIN)

        organisation_user = FFAdminUser.objects.create(email="org_user@org.com")
        organisation_user.add_organisation(self.organisation)
        url = reverse(
            "api-v1:organisations:organisation-users-update-role",
            args=[self.organisation.pk, organisation_user.pk],
        )
        data = {"role": OrganisationRole.ADMIN.name}

        # When
        res = self.client.post(url, data=data)

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and
        assert (
            organisation_user.get_organisation_role(self.organisation)
            == OrganisationRole.ADMIN.name
        )

    def test_admin_can_get_users_in_organisation(self):
        # Given
        self.user.add_organisation(self.organisation, OrganisationRole.ADMIN)

        organisation_user = FFAdminUser.objects.create(email="org_user@org.com")
        organisation_user.add_organisation(self.organisation)
        url = reverse(
            "api-v1:organisations:organisation-users-list", args=[self.organisation.pk]
        )

        # add some more users to test for N+1 issues
        for i in range(2):
            additional_user = FFAdminUser.objects.create(
                email=f"additional_user_{i}@org.com"
            )
            additional_user.add_organisation(self.organisation)

        # When
        with self.assertNumQueries(5):
            res = self.client.get(url)

        # Then
        assert res.status_code == status.HTTP_200_OK

    def test_org_user_can_get_users_in_organisation(self):
        # Given
        self.user.add_organisation(self.organisation, OrganisationRole.USER)

        organisation_user = FFAdminUser.objects.create(email="org_user@org.com")
        organisation_user.add_organisation(self.organisation)
        url = reverse(
            "api-v1:organisations:organisation-users-list", args=[self.organisation.pk]
        )

        # When
        res = self.client.get(url)

        # Then
        assert res.status_code == status.HTTP_200_OK

    def test_org_user_can_exclude_themself_when_getting_users_in_organisation(self):
        # Given
        self.user.add_organisation(self.organisation, OrganisationRole.USER)

        organisation_user = FFAdminUser.objects.create(email="org_user@org.com")
        organisation_user.add_organisation(self.organisation)
        base_url = reverse(
            "api-v1:organisations:organisation-users-list", args=[self.organisation.pk]
        )
        url = f"{base_url}?exclude_current=true"

        # When
        res = self.client.get(url)

        # Then
        assert res.status_code == status.HTTP_200_OK

        response_json = res.json()
        assert len(response_json) == 1
        assert response_json[0]["id"] == organisation_user.id


@pytest.mark.django_db
class UserPermissionGroupViewSetTestCase(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name="Test organisation")
        self.admin = FFAdminUser.objects.create(email="admin@testorganisation.com")
        self.admin.add_organisation(self.organisation, OrganisationRole.ADMIN)

        self.regular_user = FFAdminUser.objects.create(
            email="user@testorganisation.com"
        )
        self.regular_user.add_organisation(self.organisation, OrganisationRole.USER)

        self.list_url = reverse(
            "api-v1:organisations:organisation-groups-list", args=[self.organisation.id]
        )

        self.admin_user_client = APIClient()
        self.admin_user_client.force_authenticate(self.admin)

        self.regular_user_client = APIClient()
        self.regular_user_client.force_authenticate(self.regular_user)

    def _detail_url(self, permission_group_id: int) -> str:
        args = [self.organisation.id, permission_group_id]
        return reverse("api-v1:organisations:organisation-groups-detail", args=args)

    def _add_users_url(self, permission_group_id: int) -> str:
        args = [self.organisation.id, permission_group_id]
        return reverse("api-v1:organisations:organisation-groups-add-users", args=args)

    def _remove_users_url(self, permission_group_id: int) -> str:
        args = [self.organisation.id, permission_group_id]
        return reverse(
            "api-v1:organisations:organisation-groups-remove-users", args=args
        )

    def test_organisation_admin_can_interact_with_groups(self):
        client = self.admin_user_client

        # Create a group
        create_data = {"name": "Test Group"}
        create_response = client.post(self.list_url, data=create_data)
        assert create_response.status_code == status.HTTP_201_CREATED
        assert UserPermissionGroup.objects.filter(name=create_data["name"]).exists()
        group_id = create_response.json()["id"]

        # Group appears in the groups list
        list_response = client.get(self.list_url)
        assert list_response.status_code == status.HTTP_200_OK
        assert list_response.json()["results"][0]["name"] == "Test Group"

        # update the group
        update_data = {"name": "New Group Name"}
        update_response = client.patch(self._detail_url(group_id), data=update_data)
        assert update_response.status_code == status.HTTP_200_OK

        # update is reflected when getting the group
        detail_response = client.get(self._detail_url(group_id))
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.json()["name"] == update_data["name"]

        # delete the group
        delete_response = client.delete(self._detail_url(group_id))
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT
        assert not UserPermissionGroup.objects.filter(name=update_data["name"]).exists()

    def test_regular_user_cannot_interact_with_groups(self):
        client = self.regular_user_client
        group_name = "Test Group"
        group = UserPermissionGroup.objects.create(
            name=group_name, organisation=self.organisation
        )
        data = {"name": "New Test Group"}

        create_response = client.post(self.list_url, data=data)

        _404_responses = [
            client.put(self._detail_url(group.id)),
            client.get(self._detail_url(group.id)),
            client.delete(self._detail_url(group.id)),
        ]

        assert create_response.status_code == status.HTTP_403_FORBIDDEN
        assert all(
            [
                response.status_code == status.HTTP_404_NOT_FOUND
                for response in _404_responses
            ]
        )
        assert UserPermissionGroup.objects.filter(name=group_name).exists()

    def test_can_add_multiple_users_including_current_user(self):
        # Given
        group = UserPermissionGroup.objects.create(
            name="Test Group", organisation=self.organisation
        )
        url = self._add_users_url(group.id)
        data = {"user_ids": [self.admin.id, self.regular_user.id]}

        # When
        response = self.admin_user_client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert all(
            user in group.users.all() for user in [self.admin, self.regular_user]
        )

    def test_cannot_add_user_from_another_organisation(self):
        # Given
        another_organisation = Organisation.objects.create(name="Another organisation")
        another_user = FFAdminUser.objects.create(email="anotheruser@anotherorg.com")
        another_user.add_organisation(another_organisation, role=OrganisationRole.USER)
        group = UserPermissionGroup.objects.create(
            name="Test Group", organisation=self.organisation
        )
        url = self._add_users_url(group.id)
        data = {"user_ids": [another_user.id]}

        # When
        response = self.admin_user_client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_add_same_user_twice(self):
        # Given
        group = UserPermissionGroup.objects.create(
            name="Test Group", organisation=self.organisation
        )
        group.users.add(self.regular_user)
        url = self._add_users_url(group.id)
        data = {"user_ids": [self.regular_user.id]}

        # When
        self.admin_user_client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert self.regular_user in group.users.all() and group.users.count() == 1

    def test_remove_users(self):
        # Given
        group = UserPermissionGroup.objects.create(
            name="Test Group", organisation=self.organisation
        )
        group.users.add(self.regular_user, self.admin)
        url = self._remove_users_url(group.id)
        data = {"user_ids": [self.regular_user.id]}

        # When
        self.admin_user_client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        # regular user has been removed
        assert self.regular_user not in group.users.all()

        # but admin user still remains
        assert self.admin in group.users.all()

    def test_remove_users_silently_fails_if_user_not_in_group(self):
        # Given
        group = UserPermissionGroup.objects.create(
            name="Test Group", organisation=self.organisation
        )
        group.users.add(self.admin)
        url = self._remove_users_url(group.id)
        data = {"user_ids": [self.regular_user.id]}

        # When
        response = self.admin_user_client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        # request was successful
        assert response.status_code == status.HTTP_200_OK
        # and admin user is still in the group
        assert self.admin in group.users.all()


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
