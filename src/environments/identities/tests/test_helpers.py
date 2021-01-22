from unittest import mock
from unittest.case import TestCase

import pytest

from environments.identities.helpers import identify_integrations
from environments.identities.models import Identity
from environments.models import Environment
from integrations.amplitude.models import AmplitudeConfiguration
from integrations.segment.models import SegmentConfiguration
from organisations.models import Organisation, OrganisationRole
from projects.models import Project
from util.tests import Helper


@pytest.mark.django_db
class HelperTestCase(TestCase):
    identifier = "user1"

    def setUp(self):
        user = Helper.create_ffadminuser()

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
        self.identity = Identity.objects.create(
            identifier=self.identifier, environment=self.environment
        )

    @mock.patch("integrations.amplitude.amplitude.AmplitudeWrapper.identify_user_async")
    def test_identify_integrations_amplitude_called(self, mock_amplitude_wrapper):
        # Given
        # amplitude configuration for environment
        AmplitudeConfiguration.objects.create(
            api_key="abc-123", environment=self.environment
        )
        identify_integrations(self.identity, self.identity.get_all_feature_states())

        # and amplitude identify users should be called
        mock_amplitude_wrapper.assert_called()

    @mock.patch("integrations.segment.segment.SegmentWrapper.identify_user_async")
    def test_identify_integrations_segment_called(self, mock_segment_wrapper):
        # Given
        # segment configuration for environment
        SegmentConfiguration.objects.create(
            api_key="abc-123", environment=self.environment
        )
        identify_integrations(self.identity, self.identity.get_all_feature_states())

        # and segment identify users should be called
        mock_segment_wrapper.assert_called()

    @mock.patch("integrations.amplitude.amplitude.AmplitudeWrapper.identify_user_async")
    @mock.patch("integrations.segment.segment.SegmentWrapper.identify_user_async")
    def test_identify_integrations_segment_and_amplitude_called(
        self, mock_amplitude_wrapper, mock_segment_wrapper
    ):
        # Given
        SegmentConfiguration.objects.create(
            api_key="abc-123", environment=self.environment
        )
        AmplitudeConfiguration.objects.create(
            api_key="abc-123", environment=self.environment
        )
        identify_integrations(self.identity, self.identity.get_all_feature_states())

        mock_segment_wrapper.assert_called()
        mock_amplitude_wrapper.assert_called()
