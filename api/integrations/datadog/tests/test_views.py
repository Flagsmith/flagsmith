import json
from unittest.case import TestCase

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment
from integrations.datadog.models import DataDogConfiguration
from organisations.models import Organisation, OrganisationRole
from projects.models import Project
from util.tests import Helper


@pytest.mark.django_db
class DatadogConfigurationTestCase(TestCase):
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
        self.list_url = reverse(
            "api-v1:projects:integrations-datadog-list", args=[self.project.id]
        )

    def test_should_create_datadog_config_when_post(self):
        # Given setup data
        data = {"base_url": "http://test.com", "api_key": "abc-123"}

        # When
        response = self.client.post(
            self.list_url,
            data=json.dumps(data),
            content_type="application/json",
        )

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        # and
        assert DataDogConfiguration.objects.filter(project=self.project).count() == 1

    def test_should_return_BadRequest_when_duplicate_datadog_config_is_posted(self):
        # Given
        DataDogConfiguration.objects.create(
            base_url="http://test.com", api_key="api_123", project=self.project
        )
        data = {"base_url": "http://test.com", "api_key": "abc-123"}

        # When
        response = self.client.post(
            self.list_url,
            data=json.dumps(data),
            content_type="application/json",
        )

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert DataDogConfiguration.objects.filter(project=self.project).count() == 1

    #
    def test_should_update_configuration_when_put(self):
        # Given
        config = DataDogConfiguration.objects.create(
            base_url="http://test.com", api_key="api_123", project=self.project
        )
        api_key_updated = "new api"
        data = {"base_url": config.base_url, "api_key": api_key_updated}

        # When
        url = reverse(
            "api-v1:projects:integrations-datadog-detail",
            args=[self.project.id, config.id],
        )
        response = self.client.put(
            url,
            data=json.dumps(data),
            content_type="application/json",
        )
        config.refresh_from_db()

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert config.api_key == api_key_updated

    def test_should_return_datadog_config_list_when_requested(self):
        # Given - set up data

        # When
        response = self.client.get(self.list_url)

        # Then
        assert response.status_code == status.HTTP_200_OK

    def test_should_remove_configuration_when_delete(self):
        # Given
        config = DataDogConfiguration.objects.create(
            base_url="http://test.com", api_key="api_123", project=self.project
        )
        # When
        url = reverse(
            "api-v1:projects:integrations-datadog-detail",
            args=[self.project.id, config.id],
        )
        res = self.client.delete(url)

        # Then
        assert res.status_code == status.HTTP_204_NO_CONTENT
        #  and
        assert not DataDogConfiguration.objects.filter(project=self.project).exists()
