# Needs to be first to set up django environment
from .helpers import *  # isort:skip
import json

from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from environments.identities.models import Identity
from environments.models import Environment
from features.models import Feature
from organisations.models import Organisation
from projects.models import Project


class PerformanceSuite:
    test_data_count = 3
    test_iteration_count = 400

    def setup(self):
        self.client = APIClient()

        for test_data_count in range(self.test_data_count):
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
            for test_feature_count in range(self.test_data_count):
                self.feature = Feature.objects.create(
                    name="Test Feature " + str(test_feature_count), project=self.project
                )

        for test_identity_count in range(self.test_data_count):
            self.identity = Identity.objects.create(
                identifier="test-identity-" + str(test_identity_count),
                environment=self.environment,
            )

    def time_get_environment_flags(self):
        # Given
        url = reverse("api-v1:flags")
        self.client.credentials(
            HTTP_X_ENVIRONMENT_KEY=self.identity.environment.api_key
        )

        # When
        for test_flags_count in range(self.test_iteration_count):
            response = self.client.get(url)
            assert response.status_code == status.HTTP_200_OK

        # Then
        pass

    def time_get_identity_flags(self):
        # Given
        base_url = reverse("api-v1:sdk-identities")
        url = base_url + "?identifier=" + self.identity.identifier
        self.client.credentials(
            HTTP_X_ENVIRONMENT_KEY=self.identity.environment.api_key
        )

        # When
        for test_identity_count in range(self.test_iteration_count):
            response = self.client.get(url)
            assert response.status_code == status.HTTP_200_OK

        # Then
        pass

    def time_set_identity_traits_flags(self):
        # Given
        url = reverse("api-v1:sdk-identities")

        # a payload for an identity with 2 traits
        data = {
            "identifier": self.identity.identifier,
            "traits": [
                {"trait_key": "my_trait", "trait_value": 123},
                {"trait_key": "my_other_trait", "trait_value": "a value"},
            ],
        }

        # When
        # we identify that user by posting the above payload
        self.client.credentials(HTTP_X_ENVIRONMENT_KEY=self.environment.api_key)
        for test_identity_count in range(self.test_iteration_count):
            response = self.client.post(
                url, data=json.dumps(data), content_type="application/json"
            )
            print(response.status_code)
            print(response.data)
            assert response.status_code == status.HTTP_200_OK

        # Then
        pass
