from unittest import TestCase

import pytest

from environments.identities.models import Identity
from environments.models import Environment
from organisations.models import Organisation
from projects.models import Project
from segments.models import PERCENTAGE_SPLIT, Condition, Segment, SegmentRule


@pytest.mark.django_db
class SegmentRuleTest(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name="Test Org")
        self.project = Project.objects.create(
            name="Test Project", organisation=self.organisation
        )
        self.environment = Environment.objects.create(
            name="Test Environment", project=self.project
        )
        self.identity = Identity.objects.create(
            environment=self.environment, identifier="test_identity"
        )
        self.segment = Segment.objects.create(project=self.project, name="test_segment")

    def test_get_segment_returns_parent_segment_for_nested_rule(self):
        # Given
        parent_rule = SegmentRule.objects.create(
            segment=self.segment, type=SegmentRule.ALL_RULE
        )
        child_rule = SegmentRule.objects.create(
            rule=parent_rule, type=SegmentRule.ALL_RULE
        )
        grandchild_rule = SegmentRule.objects.create(
            rule=child_rule, type=SegmentRule.ALL_RULE
        )
        Condition.objects.create(
            operator=PERCENTAGE_SPLIT, value=0.1, rule=grandchild_rule
        )

        # When
        segment = grandchild_rule.get_segment()

        # Then
        assert segment == self.segment
