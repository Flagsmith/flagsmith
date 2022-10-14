import json
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from organisations.invites.models import Invite, InviteLink
from organisations.models import Organisation, OrganisationRole
from users.models import FFAdminUser


class InviteLinkViewSetTestCase(APITestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name="Test organisation")
        self.organisation_admin = FFAdminUser.objects.create(email="test@example.com")
        self.organisation_admin.add_organisation(
            self.organisation, role=OrganisationRole.ADMIN
        )
        self.client.force_authenticate(user=self.organisation_admin)

    def test_create_invite_link(self):
        # Given
        url = reverse(
            "api-v1:organisations:organisation-invite-links-list",
            args=[self.organisation.pk],
        )
        tomorrow = timezone.now() + timedelta(days=1)
        data = {"expires_at": tomorrow.strftime("%Y-%m-%d %H:%M:%S")}

        # When
        response = self.client.post(url, data=data)

        # Then
        assert response.status_code == status.HTTP_201_CREATED

        response_json = response.json()
        expected_attributes = ("hash", "id", "expires_at", "role")
        assert all(attr in response_json for attr in expected_attributes)

    def test_get_invite_links_for_organisation(self):
        # Given
        url = reverse(
            "api-v1:organisations:organisation-invite-links-list",
            args=[self.organisation.pk],
        )
        for role in OrganisationRole:
            InviteLink.objects.create(organisation=self.organisation, role=role.name)

        # When
        response = self.client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK

        response_json = response.json()
        assert len(response_json) == 2
        expected_attributes = ("hash", "id", "expires_at")
        for invite_link in response_json:
            assert all(attr in invite_link for attr in expected_attributes)

    def test_delete_invite_link_for_organisation(self):
        # Given
        invite = InviteLink.objects.create(organisation=self.organisation)
        url = reverse(
            "api-v1:organisations:organisation-invite-links-detail",
            args=[self.organisation.pk, invite.pk],
        )

        # When
        response = self.client.delete(url)

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT


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


def test_create_invite_link_with_permission_group(
    admin_client, organisation, test_user_client, user_permission_group
):
    # Given
    url = reverse(
        "api-v1:organisations:organisation-invite-links-list",
        args=[organisation.pk],
    )
    tomorrow = timezone.now() + timedelta(days=1)
    data = {
        "expires_at": tomorrow.strftime("%Y-%m-%d %H:%M:%S"),
        "permission_groups": [user_permission_group.id],
    }

    # When
    response = admin_client.post(url, data=data)

    # Then
    assert response.status_code == status.HTTP_201_CREATED

    response_json = response.json()
    assert response_json["permission_groups"] == [user_permission_group.id]


def test_join_organisation_with_permission_groups(
    test_user, test_user_client, organisation, user_permission_group
):
    # Given
    invite = Invite.objects.create(email=test_user.email, organisation=organisation)
    invite.permission_groups.add(user_permission_group)

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


def test_join_organisation_via_link_with_permission_groups(
    test_user, organisation, test_user_client, user_permission_group
):
    # Given
    invite = InviteLink.objects.create(organisation=organisation)
    invite.permission_groups.add(user_permission_group)

    url = reverse("api-v1:users:user-join-organisation-link", args=[invite.hash])

    # When
    response = test_user_client.post(url)
    test_user.refresh_from_db()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert organisation in test_user.organisations.all()
    assert user_permission_group in test_user.permission_groups.all()


def test_create_invite_with_permission_groups(
    admin_client, organisation, user_permission_group, admin_user
):
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
    assert response.status_code == status.HTTP_201_CREATED
    # and
    invite = Invite.objects.get(email=email)
    assert invite.permission_groups.first() == user_permission_group
    assert invite.invited_by == admin_user


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
