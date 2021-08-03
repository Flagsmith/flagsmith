import pytest
from django.test import TestCase

from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import STRING, Environment
from features.models import (
    Feature,
    FeatureSegment,
    FeatureState,
    FeatureStateValue,
)
from features.utils import BOOLEAN, INTEGER
from organisations.models import Organisation
from projects.models import Project
from segments.models import EQUAL, Condition, Segment, SegmentRule


@pytest.mark.django_db
class FeatureSegmentTest(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name="Test org")
        self.project = Project.objects.create(
            name="Test project", organisation=self.organisation
        )
        self.environment = Environment.objects.create(
            name="Test environment", project=self.project
        )

        self.initial_value = "test"
        self.remote_config = Feature.objects.create(
            name="Remote Config",
            initial_value="test",
            project=self.project,
        )

        self.segment = Segment.objects.create(name="Test segment", project=self.project)
        segment_rule = SegmentRule.objects.create(
            segment=self.segment, type=SegmentRule.ALL_RULE
        )

        self.condition_property = "test_property"
        self.condition_value = "test_value"
        Condition.objects.create(
            property=self.condition_property,
            value=self.condition_value,
            operator=EQUAL,
            rule=segment_rule,
        )

        self.matching_identity = Identity.objects.create(
            identifier="user_1", environment=self.environment
        )
        Trait.objects.create(
            identity=self.matching_identity,
            trait_key=self.condition_property,
            value_type=STRING,
            string_value=self.condition_value,
        )

        self.not_matching_identity = Identity.objects.create(
            identifier="user_2", environment=self.environment
        )

    def test_feature_segment_is_less_than_other_if_priority_lower(self):
        # Given
        feature_segment_1 = FeatureSegment.objects.create(
            feature=self.remote_config,
            segment=self.segment,
            environment=self.environment,
            priority=1,
        )

        another_segment = Segment.objects.create(
            name="Another segment", project=self.project
        )
        feature_segment_2 = FeatureSegment.objects.create(
            feature=self.remote_config,
            segment=another_segment,
            environment=self.environment,
            priority=2,
        )

        # When
        result = feature_segment_2 < feature_segment_1

        # Then
        assert result

    def test_feature_segments_are_created_with_correct_priority(self):
        # Given - 5 feature segments

        # 2 with the same feature, environment but a different segment
        another_segment = Segment.objects.create(
            name="Another segment", project=self.project
        )
        feature_segment_1 = FeatureSegment.objects.create(
            feature=self.remote_config,
            segment=self.segment,
            environment=self.environment,
        )

        feature_segment_2 = FeatureSegment.objects.create(
            feature=self.remote_config,
            segment=another_segment,
            environment=self.environment,
        )

        # 1 with the same feature but a different environment
        another_environment = Environment.objects.create(
            name="Another environment", project=self.project
        )
        feature_segment_3 = FeatureSegment.objects.create(
            feature=self.remote_config,
            segment=self.segment,
            environment=another_environment,
        )

        # 1 with the same environment but a different feature
        another_feature = Feature.objects.create(
            name="Another feature", project=self.project
        )
        feature_segment_4 = FeatureSegment.objects.create(
            feature=another_feature, segment=self.segment, environment=self.environment
        )

        # 1 with a different feature and a different environment
        feature_segment_5 = FeatureSegment.objects.create(
            feature=another_feature,
            segment=self.segment,
            environment=another_environment,
        )

        # Then
        # the two with the same feature and environment are created with ascending priorities
        assert feature_segment_1.priority == 0
        assert feature_segment_2.priority == 1

        # the ones with different combinations of features and environments are all created with a priority of 0
        assert feature_segment_3.priority == 0
        assert feature_segment_4.priority == 0
        assert feature_segment_5.priority == 0

    def test_clone_creates_a_new_object(self):
        # Given
        feature_segment = FeatureSegment.objects.create(
            feature=self.remote_config,
            segment=self.segment,
            environment=self.environment,
            priority=1,
        )
        new_env = Environment.objects.create(
            name="Test environment New", project=self.project
        )

        # When
        feature_segment_clone = feature_segment.clone(new_env)

        # Then
        assert feature_segment_clone.id != feature_segment.id
        assert feature_segment_clone.priority == feature_segment.priority
