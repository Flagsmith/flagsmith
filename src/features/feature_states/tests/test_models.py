from unittest import mock

import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase

from environments.identities.models import Identity
from environments.models import Environment
from features.feature_states.models import FeatureState
from features.models import Feature, FeatureSegment
from organisations.models import Organisation
from projects.models import Project
from segments.models import Segment


@pytest.mark.django_db
class FeatureStateTest(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name="Test org")
        self.project = Project.objects.create(
            name="Test project", organisation=self.organisation
        )
        self.environment = Environment.objects.create(
            name="Test environment", project=self.project
        )
        self.feature = Feature.objects.create(name="Test feature", project=self.project)

    @mock.patch("features.feature_states.models.trigger_feature_state_change_webhooks")
    def test_cannot_create_duplicate_feature_state_in_an_environment(
        self, mock_trigger_webhooks
    ):
        """
        Note that although the mock isn't used in this test, it throws an exception
        on it's thread so we mock it here anyway.
        """
        # Given
        duplicate_feature_state = FeatureState(
            feature=self.feature, environment=self.environment, enabled=True
        )

        # When
        with pytest.raises(ValidationError):
            duplicate_feature_state.save()

        # Then
        assert (
            FeatureState.objects.filter(
                feature=self.feature, environment=self.environment
            ).count()
            == 1
        )

    def test_feature_state_gt_operator(self):
        # Given
        identity = Identity.objects.create(
            identifier="test_identity", environment=self.environment
        )
        segment_1 = Segment.objects.create(name="Test Segment 1", project=self.project)
        segment_2 = Segment.objects.create(name="Test Segment 2", project=self.project)
        feature_segment_p1 = FeatureSegment.objects.create(
            segment=segment_1,
            feature=self.feature,
            environment=self.environment,
            priority=1,
        )
        feature_segment_p2 = FeatureSegment.objects.create(
            segment=segment_2,
            feature=self.feature,
            environment=self.environment,
            priority=2,
        )

        # When
        identity_state = FeatureState.objects.create(
            identity=identity, feature=self.feature, environment=self.environment
        )

        segment_1_state = FeatureState.objects.get(
            feature_segment=feature_segment_p1,
            feature=self.feature,
            environment=self.environment,
        )
        segment_2_state = FeatureState.objects.get(
            feature_segment=feature_segment_p2,
            feature=self.feature,
            environment=self.environment,
        )
        default_env_state = FeatureState.objects.get(
            environment=self.environment, identity=None, feature_segment=None
        )

        # Then - identity state is higher priority than all
        assert identity_state > segment_1_state
        assert identity_state > segment_2_state
        assert identity_state > default_env_state

        # and feature state with feature segment with highest priority is greater than feature state with lower
        # priority feature segment and default environment state
        assert segment_1_state > segment_2_state
        assert segment_1_state > default_env_state

        # and feature state with any segment is greater than default environment state
        assert segment_2_state > default_env_state

    def test_feature_state_gt_operator_throws_value_error_if_different_environments(
        self,
    ):
        # Given
        another_environment = Environment.objects.create(
            name="Another environment", project=self.project
        )
        feature_state_env_1 = FeatureState.objects.filter(
            environment=self.environment
        ).first()
        feature_state_env_2 = FeatureState.objects.filter(
            environment=another_environment
        ).first()

        # When
        with pytest.raises(ValueError):
            result = feature_state_env_1 > feature_state_env_2

        # Then - exception raised

    def test_feature_state_gt_operator_throws_value_error_if_different_features(self):
        # Given
        another_feature = Feature.objects.create(
            name="Another feature", project=self.project
        )
        feature_state_env_1 = FeatureState.objects.filter(feature=self.feature).first()
        feature_state_env_2 = FeatureState.objects.filter(
            feature=another_feature
        ).first()

        # When
        with pytest.raises(ValueError):
            result = feature_state_env_1 > feature_state_env_2

        # Then - exception raised

    def test_feature_state_gt_operator_throws_value_error_if_different_identities(self):
        # Given
        identity_1 = Identity.objects.create(
            identifier="identity_1", environment=self.environment
        )
        identity_2 = Identity.objects.create(
            identifier="identity_2", environment=self.environment
        )

        feature_state_identity_1 = FeatureState.objects.create(
            feature=self.feature, environment=self.environment, identity=identity_1
        )
        feature_state_identity_2 = FeatureState.objects.create(
            feature=self.feature, environment=self.environment, identity=identity_2
        )

        # When
        with pytest.raises(ValueError):
            result = feature_state_identity_1 > feature_state_identity_2

        # Then - exception raised

    @mock.patch("features.feature_states.models.trigger_feature_state_change_webhooks")
    def test_save_calls_trigger_webhooks(self, mock_trigger_webhooks):
        # Given
        feature_state = FeatureState.objects.get(
            feature=self.feature, environment=self.environment
        )

        # When
        feature_state.save()

        # Then
        mock_trigger_webhooks.assert_called_with(feature_state)
