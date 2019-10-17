from unittest import TestCase, mock
from unittest.mock import MagicMock

import pytest
from rest_framework.exceptions import AuthenticationFailed

from environments.authentication import EnvironmentKeyAuthentication
from environments.models import Environment
from organisations.models import Organisation
from projects.models import Project


@pytest.mark.django_db
class EnvironmentKeyAuthenticationTestCase(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name='Test org')
        self.project = Project.objects.create(name='Test project', organisation=self.organisation)
        self.environment = Environment.objects.create(name='Test environment', project=self.project)

        self.authenticator = EnvironmentKeyAuthentication()

    def test_authentication_passes_if_valid_api_key_passed(self):
        # Given
        request = MagicMock()
        request.META.get.return_value = self.environment.api_key

        # When
        self.authenticator.authenticate(request)

        # Then - authentication passes
        pass

    def test_authenticate_raises_authentication_failed_if_request_missing_environment_key(self):
        # Given
        request = MagicMock()

        # When / Then
        with pytest.raises(AuthenticationFailed):
            self.authenticator.authenticate(request)

    def test_authenticate_raises_authentication_failed_if_request_environment_key_not_found(self):
        # Given
        request = MagicMock()
        request.META.get.return_value = 'some-invalid-key'

        # When / Then
        with pytest.raises(AuthenticationFailed):
            self.authenticator.authenticate(request)

    def test_authenticate_raises_authentication_failed_if_organisation_set_to_stop_serving_flags(self):
        # Given
        self.organisation.stop_serving_flags = True
        self.organisation.save()

        request = MagicMock()
        request.META.get.return_value = self.environment.api_key

        # When / Then
        with pytest.raises(AuthenticationFailed):
            self.authenticator.authenticate(request)
