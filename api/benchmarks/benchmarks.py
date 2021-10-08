# Needs to be first to set up django environment
from .helpers import *  # isort:skip

from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from environments.identities.models import Identity
from environments.models import Environment
from features.models import Feature, FeatureSegment, FeatureState
from organisations.models import Organisation
from projects.models import Project
from segments.models import Segment


class PerformanceSuite:
    def setup(self):
        self.client = APIClient()

        for test_data_count in range(3):
            self.organisation = Organisation.objects.create(
                name="Performance Test Organisation " + str(test_data_count)
            )
            self.project = Project.objects.create(
                name="Performance Test Project " + str(test_data_count),
                organisation=self.organisation,
            )
            self.environment = Environment.objects.create(
                name="Performance Test Environment " + str(test_data_count),
                project=self.project,
            )
            for test_feature_count in range(10):
                self.feature = Feature.objects.create(
                    name="Test Feature " + str(test_feature_count), project=self.project
                )

        for test_identity_count in range(5):
            self.identity = Identity.objects.create(
                identifier="test-identity-" + str(test_identity_count),
                environment=self.environment,
            )

    def time_keys(self):
        # Given
        base_url = reverse("api-v1:sdk-identities")
        url = base_url + "?identifier=" + self.identity.identifier

        # When
        self.client.credentials(
            HTTP_X_ENVIRONMENT_KEY=self.identity.environment.api_key
        )

        for test_identity_count in range(400):
            response = self.client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK

        # and
        # assert len(response.json().get("flags")) == 2

        pass
