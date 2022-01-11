from unittest import mock
from unittest.case import TestCase

import pytest

from environments.identities.models import Identity
from environments.models import Environment
from integrations.amplitude.models import AmplitudeConfiguration
from integrations.integration import identify_integrations
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


def test_identify_integrations_calls_every_integration_in_identity_integrations_dict(
    mocker, identity
):
    # Given
    integration_wrapper_a = mocker.MagicMock()
    integration_wrapper_b = mocker.MagicMock()

    integration_a_config = mocker.MagicMock()
    integration_b_config = mocker.MagicMock()

    identity.environment.integration_a_config = integration_a_config
    identity.environment.integration_b_config = integration_b_config

    identity_integrations = [
        {"relation_name": "integration_a_config", "wrapper": integration_wrapper_a},
        {"relation_name": "integration_b_config", "wrapper": integration_wrapper_b},
    ]
    mocker.patch(
        "integrations.integration.IDENTITY_INTEGRATIONS", identity_integrations
    )

    # When
    identify_integrations(identity, identity.get_all_feature_states())

    # Then
    # Integration a was successfully called

    integration_wrapper_a.assert_called_with(integration_a_config)

    integration_a_mocked_generate_user_data = (
        integration_wrapper_a.return_value.generate_user_data
    )

    integration_a_mocked_generate_user_data.assert_called_with(
        identity=identity, feature_states=identity.get_all_feature_states()
    )
    integration_wrapper_a.return_value.identify_user_async.assert_called_with(
        data=integration_a_mocked_generate_user_data.return_value
    )

    # Integration b was successfully called
    integration_wrapper_b.assert_called_with(integration_b_config)

    integration_b_mocked_generate_user_data = (
        integration_wrapper_b.return_value.generate_user_data
    )

    integration_b_mocked_generate_user_data.assert_called_with(
        identity=identity, feature_states=identity.get_all_feature_states()
    )
    integration_wrapper_b.return_value.identify_user_async.assert_called_with(
        data=integration_b_mocked_generate_user_data.return_value
    )
