import json
from datetime import datetime, timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from organisations.invites.models import InviteLink
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

    def test_update_invite_link_for_organisation(self):
        # Given
        invite = InviteLink.objects.create(organisation=self.organisation)
        url = reverse(
            "api-v1:organisations:organisation-invite-links-detail",
            args=[self.organisation.pk, invite.pk],
        )
        tomorrow = timezone.now() + timedelta(days=1)
        data = {"expires_at": tomorrow.isoformat()}

        # When
        response = self.client.patch(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert response.status_code == status.HTTP_200_OK

        response_json = response.json()

        # convert the returned dt in the json to python dt format before comparison
        returned_expires_at = response_json["expires_at"]
        expires_at = returned_expires_at.replace("Z", "+00:00")

        assert expires_at == tomorrow.isoformat()

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
