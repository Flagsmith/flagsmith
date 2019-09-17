import pytest
from django.db.utils import IntegrityError
from django.test import TestCase

from environments.models import Environment, Identity, Trait, STRING
from features.models import Feature, FeatureState, CONFIG, FeatureSegment, FeatureStateValue
from organisations.models import Organisation
from projects.models import Project
from segments.models import Segment, SegmentRule, Condition, EQUAL


@pytest.mark.django_db
class FeatureTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organisation = Organisation.objects.create(name="Test Org")
        cls.project = Project.objects.create(name="Test Project", organisation=cls.organisation)
        cls.environment_one = Environment.objects.create(name="Test Environment 1",
                                                         project=cls.project)
        cls.environment_two = Environment.objects.create(name="Test Environment 2",
                                                         project=cls.project)

    def test_feature_should_create_feature_states_for_environments(self):
        feature = Feature.objects.create(name="Test Feature", project=self.project)

        feature_states = FeatureState.objects.filter(feature=feature)

        self.assertEquals(feature_states.count(), 2)

    def test_creating_feature_with_initial_value_should_set_value_for_all_feature_states(self):
        feature = Feature.objects.create(name="Test Feature", project=self.project,
                                         initial_value="This is a value")

        feature_states = FeatureState.objects.filter(feature=feature)

        for feature_state in feature_states:
            self.assertEquals(feature_state.get_feature_state_value(), "This is a value")

    def test_updating_feature_state_should_trigger_webhook(self):
        feature = Feature.objects.create(name="Test Feature", project=self.project)
        # TODO: implement webhook test method

    def test_cannot_create_feature_with_same_case_insensitive_name(self):
        # Given
        feature_name = 'Test Feature'

        feature_one = Feature(project=self.project, name=feature_name)
        feature_two = Feature(project=self.project, name=feature_name.lower())

        # When
        feature_one.save()

        # Then
        with pytest.raises(IntegrityError):
            feature_two.save()


@pytest.mark.django_db
class FeatureSegmentTest(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name='Test org')
        self.project = Project.objects.create(name='Test project', organisation=self.organisation)
        self.environment = Environment.objects.create(name='Test environment', project=self.project)

        self.initial_value = 'test'
        self.remote_config = Feature.objects.create(name='Remote Config', type=CONFIG, initial_value='test',
                                                    project=self.project)

        self.segment = Segment.objects.create(name='Test segment', project=self.project)
        segment_rule = SegmentRule.objects.create(segment=self.segment, type=SegmentRule.ALL_RULE)

        self.condition_property = 'test_property'
        self.condition_value = 'test_value'
        Condition.objects.create(property=self.condition_property, value=self.condition_value,
                                 operator=EQUAL, rule=segment_rule)

        self.matching_identity = Identity.objects.create(identifier='user_1', environment=self.environment)
        Trait.objects.create(identity=self.matching_identity, trait_key=self.condition_property, value_type=STRING,
                             string_value=self.condition_value)

        self.not_matching_identity = Identity.objects.create(identifier='user_2', environment=self.environment)

    def test_can_create_segment_override_for_remote_config(self):
        # Given
        overridden_value = 'overridden value'
        feature_segment = FeatureSegment.objects.create(feature=self.remote_config, segment=self.segment, priority=1)
        FeatureStateValue.objects.filter(
            feature_state__feature_segment=feature_segment).update(type=STRING, string_value=overridden_value)

        # When
        feature_states = self.matching_identity.get_all_feature_states()

        # Then
        assert feature_states.get(feature=self.remote_config).get_feature_state_value() == overridden_value

    def test_feature_state_enabled_value_is_updated_when_feature_segment_updated(self):
        # Given
        feature_segment = FeatureSegment.objects.create(feature=self.remote_config, segment=self.segment, priority=1)
        feature_state = FeatureState.objects.get(feature_segment=feature_segment, enabled=False)

        # When
        feature_segment.enabled = True
        feature_segment.save()

        # Then
        feature_state.refresh_from_db()
        assert feature_state.enabled

