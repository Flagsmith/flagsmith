from unittest import TestCase, mock

import pytest

import segments
from environments.models import Identity, Environment
from organisations.models import Organisation
from projects.models import Project
from segments.models import Segment, SegmentRule, PERCENTAGE_SPLIT, Condition


@pytest.mark.django_db
class SegmentTestCase(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name='Test Org')
        self.project = Project.objects.create(name='Test Project', organisation=self.organisation)
        self.environment = Environment.objects.create(name='Test Environment', project=self.project)
        self.identity = Identity.objects.create(environment=self.environment, identifier='test_identity')

    def tearDown(self) -> None:
        Segment.objects.all().delete()
        Identity.objects.all().delete()

    def test_percentage_value_for_given_segment_rule_and_identity_is_number_between_0_and_1(self):
        # Given
        segment = Segment.objects.create(name='Test Segment', project=self.project)

        # When
        result = segment.get_identity_percentage_value(self.identity)

        # Then
        assert 1 >= result >= 0

    def test_percentage_value_for_given_segment_rule_and_identity_is_the_same_each_time(self):
        # Given
        segment = Segment.objects.create(name='Test Segment', project=self.project)

        # When
        result_1 = segment.get_identity_percentage_value(self.identity)
        result_2 = segment.get_identity_percentage_value(self.identity)

        # Then
        assert result_1 == result_2

    def test_percentage_value_is_unique_for_different_identities(self):
        # Given
        segment = Segment.objects.create(name='Test Segment', project=self.project)
        another_identity = Identity.objects.create(environment=self.environment, identifier='another_test_identity')

        # When
        result_1 = segment.get_identity_percentage_value(self.identity)
        result_2 = segment.get_identity_percentage_value(another_identity)

        # Then
        assert result_1 != result_2

    def test_percentage_values_should_be_evenly_distributed(self):
        """
        This test checks if the percentage value returned by the method on SegmentRule returns evenly distributed
        values.

        Note that since it's technically random, it's not guaranteed to pass every time, however, it should pass
        99/100 times. It will likely be more accurate by increasing the test_sample value and / or decreasing
        the num_test_buckets value.
        """
        test_sample = 10000  # number of identities to create to test with
        num_test_buckets = 10  # split the sample into 'buckets' to check that the values are evenly distributed
        test_bucket_size = int(test_sample / num_test_buckets)
        error_factor = 0.1

        # Given
        segment = Segment.objects.create(name='Test Segment', project=self.project)
        identities = []
        for i in range(test_sample):
            identities.append(Identity(environment=self.environment, identifier=str(i)))
        Identity.objects.bulk_create(identities)

        # When
        values = [segment.get_identity_percentage_value(identity) for identity in Identity.objects.all()]
        values.sort()

        # Then
        for j in range(num_test_buckets):
            bucket_start = j * test_bucket_size
            bucket_end = (j + 1) * test_bucket_size
            bucket_value_limit = min((j + 1) / num_test_buckets + error_factor * ((j + 1) / num_test_buckets), 1)

            assert all([value <= bucket_value_limit for value in values[bucket_start:bucket_end]])


@pytest.mark.django_db
class SegmentRuleTest(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name='Test Org')
        self.project = Project.objects.create(name='Test Project', organisation=self.organisation)
        self.environment = Environment.objects.create(name='Test Environment', project=self.project)
        self.identity = Identity.objects.create(environment=self.environment, identifier='test_identity')
        self.segment = Segment.objects.create(project=self.project, name='test_segment')

    def test_get_segment_returns_parent_segment_for_nested_rule(self):
        # Given
        parent_rule = SegmentRule.objects.create(segment=self.segment, type=SegmentRule.ALL_RULE)
        child_rule = SegmentRule.objects.create(rule=parent_rule, type=SegmentRule.ALL_RULE)
        grandchild_rule = SegmentRule.objects.create(rule=child_rule, type=SegmentRule.ALL_RULE)
        Condition.objects.create(operator=PERCENTAGE_SPLIT, value=0.1, rule=grandchild_rule)

        # When
        segment = grandchild_rule.get_segment()

        # Then
        assert segment == self.segment


@pytest.mark.django_db
class ConditionTest(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name='Test Org')
        self.project = Project.objects.create(name='Test Project', organisation=self.organisation)
        self.environment = Environment.objects.create(name='Test Environment', project=self.project)
        self.identity = Identity.objects.create(environment=self.environment, identifier='test_identity')
        self.segment = Segment.objects.create(project=self.project, name='test_segment')
        self.rule = SegmentRule.objects.create(segment=self.segment, type=SegmentRule.ALL_RULE)

    @mock.patch.object(segments.models.Segment, 'get_identity_percentage_value')
    def test_percentage_split_calculation_divides_value_by_100_before_comparison(self, get_identity_percentage_value):
        # Given
        condition = Condition.objects.create(rule=self.rule, operator=PERCENTAGE_SPLIT, value=10)
        get_identity_percentage_value.return_value = 0.2

        # When
        res = condition.does_identity_match(self.identity)

        # Then
        assert not res


