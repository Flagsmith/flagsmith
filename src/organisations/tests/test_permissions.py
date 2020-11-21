from unittest import TestCase, mock

import pytest

from organisations.models import Organisation, OrganisationRole
from organisations.permissions import OrganisationUsersPermission
from users.models import FFAdminUser

mock_request = mock.MagicMock
mock_view = mock.MagicMock


@pytest.mark.django_db
class OrganisationUsersPermissionTestCase(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name="Test")
        self.user = FFAdminUser.objects.create(email="user@test.com")
        self.org_admin = FFAdminUser.objects.create(email="admin@test.com")

        self.user.add_organisation(self.organisation)
        self.org_admin.add_organisation(self.organisation, OrganisationRole.ADMIN)

        self.permissions = OrganisationUsersPermission()

        mock_view.kwargs = {"organisation_pk": self.organisation.id}

    def test_org_user_can_list_users(self):
        # Given
        mock_request.user = self.user
        mock_view.action = "list"

        # When
        result = self.permissions.has_permission(mock_request, mock_view)

        # Then
        assert result

    def test_org_user_cannot_create_user(self):
        # Given
        mock_request.user = self.user
        mock_view.action = "create"

        # When
        result = self.permissions.has_permission(mock_request, mock_view)

        # Then
        assert not result
