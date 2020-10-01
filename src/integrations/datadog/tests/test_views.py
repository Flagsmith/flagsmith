from unittest.case import TestCase

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment
from integrations.datadog.models import DataDogConfiguration
from organisations.models import Organisation, OrganisationRole
from projects.models import Project
from util.tests import Helper


@pytest.mark.django_db
class DatadogConfigurationTestCase(TestCase):
    post_put_template = '{ "base_url" : "%s", "api_key" : "%s" }'
    datadog_config_url = "/projects/%d/integrations/datadog/"
    datadog_config_detail_url = datadog_config_url + "%d/"

    def setUp(self):
        self.client = APIClient()
        user = Helper.create_ffadminuser()
        self.client.force_authenticate(user=user)

        self.organisation = Organisation.objects.create(name="Test Org")
        user.add_organisation(
            self.organisation, OrganisationRole.ADMIN
        )  # admin to bypass perms

        self.project = Project.objects.create(
            name="Test project", organisation=self.organisation
        )
        self.environment = Environment.objects.create(
            name="Test Environment", project=self.project
        )

    def test_should_create_datadog_config_when_post(self):
        # Given setup data

        # When
        response = self.client.post(
            self.datadog_config_url % self.project.id,
            data=self.post_put_template % ("http://test.com", "abc-123"),
            content_type="application/json",
        )

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        # and
        assert DataDogConfiguration.objects.filter(project=self.project).count() == 1

    def test_should_return_BadRequest_when_duplicate_datadog_config_is_posted(self):
        # Given
        config = DataDogConfiguration.objects.create(base_url="http://test.com",
                                                     api_key="api_123",
                                                     project=self.project)

        # When
        response = self.client.post(
            self.datadog_config_url % self.project.id,
            data=self.post_put_template % ("http://test.com", "abc-123"),
            content_type="application/json",
        )

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert DataDogConfiguration.objects.filter(project=self.project).count() == 1

    #
    def test_should_update_configuration_when_put(self):
        # Given
        config = DataDogConfiguration.objects.create(base_url="http://test.com",
                                                     api_key="api_123",
                                                     project=self.project)
        api_key_updated = "new api"

        # When
        response = self.client.put(
            self.datadog_config_detail_url % (self.project.id, config.id),
            data=self.post_put_template % (api_key_updated, "http://test.com"),
            content_type="application/json",
        )
        config.refresh_from_db()

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert config.api_key == api_key_updated

    def test_should_return_amplitude_config_list_when_requested(self):
        # Given - set up data

        # When
        response = self.client.get(
            self.datadog_config_url % self.project.id
        )

        # Then
        assert response.status_code == status.HTTP_200_OK

    def test_should_remove_configuration_when_delete(self):
        # Given
        config = DataDogConfiguration.objects.create(base_url="http://test.com",
                                                     api_key="api_123",
                                                     project=self.project)
        # When
        res = self.client.delete(
            self.datadog_config_detail_url % (self.project.id, config.id),
            content_type="application/json",
        )

        # Then
        assert res.status_code == status.HTTP_204_NO_CONTENT
        #  and
        assert not DataDogConfiguration.objects.filter(project=self.project).exists()
