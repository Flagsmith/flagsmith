from unittest import TestCase

import pytest

from environments.models import UserEnvironmentPermission, EnvironmentPermissionModel, Environment
from organisations.models import Organisation, OrganisationRole
from projects.models import Project, UserProjectPermission, ProjectPermissionModel
from users.models import FFAdminUser


@pytest.mark.django_db
class FFAdminUserTestCase(TestCase):
    def setUp(self) -> None:
        self.user = FFAdminUser.objects.create(email="test@example.com")
        self.organisation = Organisation.objects.create(name="Test Organisation")

        self.project_1 = Project.objects.create(name='Test project 1', organisation=self.organisation)
        self.project_2 = Project.objects.create(name='Test project 2', organisation=self.organisation)

        self.environment_1 = Environment.objects.create(name='Test Environment 1', project=self.project_1)
        self.environment_2 = Environment.objects.create(name='Test Environment 2', project=self.project_2)

    def test_user_belongs_to_success(self):
        self.user.add_organisation(self.organisation, OrganisationRole.USER)
        assert self.user.belongs_to(self.organisation.id)

    def test_user_belongs_to_fail(self):
        assert not self.user.belongs_to(self.organisation.id)

    def test_get_permitted_projects_for_org_admin_returns_all_projects(self):
        # Given
        self.user.add_organisation(self.organisation, OrganisationRole.ADMIN)

        # When
        projects = self.user.get_permitted_projects(['VIEW_PROJECT', 'CREATE_ENVIRONMENT'])

        # Then
        assert projects.count() == 2

    def test_get_permitted_projects_for_user_returns_only_projects_matching_permission(self):
        # Given
        self.user.add_organisation(self.organisation, OrganisationRole.USER)
        user_project_permission = UserProjectPermission.objects.create(user=self.user, project=self.project_1)
        read_permission = ProjectPermissionModel.objects.get(key='VIEW_PROJECT')
        user_project_permission.permissions.set([read_permission])

        # When
        projects = self.user.get_permitted_projects(permissions=['VIEW_PROJECT'])

        # Then
        assert projects.count() == 1

    def test_get_admin_organisations(self):
        # Given
        self.user.add_organisation(self.organisation, OrganisationRole.ADMIN)

        # When
        admin_orgs = self.user.get_admin_organisations()

        # Then
        assert self.organisation in admin_orgs

    def test_get_permitted_environments_for_org_admin_returns_all_environments(self):
        # Given
        self.user.add_organisation(self.organisation, OrganisationRole.ADMIN)

        # When
        environments = self.user.get_permitted_environments(['VIEW_ENVIRONMENT'])

        # Then
        assert environments.count() == 2

    def test_get_permitted_environments_for_user_returns_only_environments_matching_permission(self):
        # Given
        self.user.add_organisation(self.organisation, OrganisationRole.USER)
        user_environment_permission = UserEnvironmentPermission.objects.create(user=self.user, environment=self.environment_1)
        read_permission = EnvironmentPermissionModel.objects.get(key='VIEW_ENVIRONMENT')
        user_environment_permission.permissions.set([read_permission])

        # When
        environments = self.user.get_permitted_environments(permissions=['VIEW_ENVIRONMENT'])

        # Then
        assert environments.count() == 1
