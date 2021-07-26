import json
from unittest import mock
from unittest.case import TestCase

import pytest
from dateutil.relativedelta import relativedelta
from django.test import Client as DjangoClient
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from organisations.invites.models import Invite, InviteLink
from organisations.models import Organisation, OrganisationRole, Subscription
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
        assert self.user.is_admin(self.organisation)

    @mock.patch("organisations.invites.views.Thread")
    def test_join_organisation_alerts_admin_users_if_exceeds_plan_limit(
        self, MockThread
    ):
        # Given
        Subscription.objects.create(organisation=self.organisation, max_seats=1)
        invite = Invite.objects.create(
            email=self.user.email, organisation=self.organisation
        )
        url = reverse("api-v1:users:user-join-organisation", args=[invite.hash])

        existing_org_user = FFAdminUser.objects.create(
            email="existing_org_user@example.com"
        )
        existing_org_user.add_organisation(self.organisation, OrganisationRole.USER)

        # When
        self.client.post(url)

        # Then
        MockThread.assert_called_with(
            target=FFAdminUser.send_organisation_over_limit_alert,
            args=[self.organisation],
        )

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

        # When
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

        responses = [
            client.post(self.list_url, data=data),
            client.put(self._detail_url(group.id)),
            client.get(self._detail_url(group.id)),
            client.delete(self._detail_url(group.id)),
        ]

        assert all(
            [
                response.status_code == status.HTTP_403_FORBIDDEN
                for response in responses
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


@pytest.mark.django_db
class InitialConfigurationTestCase(TestCase):
    def setUp(self):
        self.client = DjangoClient()

    def tearDown(self) -> None:
        Helper.clean_up()

    def test_returns_302_when_user_exists_but_is_not_logged_in(self):
        # Given
        self.user = Helper.create_ffadminuser()
        url = reverse("api-v1:users:config-init")

        # When
        get_response = self.client.get(url)
        post_response = self.client.get(url)

        # Then
        assert get_response.status_code == status.HTTP_302_FOUND
        assert post_response.status_code == status.HTTP_302_FOUND

    def test_returns_403_when_user_exists_and_is_not_logged_in(self):
        # Given
        self.user = Helper.create_ffadminuser()
        self.client.force_login(user=self.user)

        url = reverse("api-v1:users:config-init")

        # When
        get_response = self.client.get(url)

        post_response = self.client.get(url)

        # Then
        assert get_response.status_code == status.HTTP_403_FORBIDDEN
        assert post_response.status_code == status.HTTP_403_FORBIDDEN

    def test_returns_200_when_no_user_exists(self):
        # Given
        url = reverse("api-v1:users:config-init")

        # When
        response = self.client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
