import uuid
from unittest.mock import patch, MagicMock

import pytest
from django.contrib.contenttypes.models import ContentType
from flag_engine.segments.constants import EQUAL, CONTAINS, GREATER_THAN

from features.workflows.core.models import ChangeRequest
from metadata.models import Metadata, MetadataModelField
from projects.models import Project
from segments.models import Segment, SegmentRule, Condition
from segments.services import SegmentCloner


def test_shallow_clone(project: Project, segment: Segment) -> None:
    # Given
    # Create a real ChangeRequest object
    change_request = ChangeRequest.objects.create(
        project=project, title="Test change request", user=None
    )

    # Initialize the service
    cloner = SegmentCloner(segment)

    # When - properly mock the history attribute and its update method
    with patch.object(Segment, "history", create=True) as mock_history:
        # Setup the mock to have an update method
        mock_update = MagicMock()
        mock_history.update = mock_update

        # Call the method under test
        cloned_segment = cloner.shallow_clone(
            name="Shallow Cloned Segment",
            description="New description",
            change_request=change_request,
        )

        # Verify history update was called
        mock_update.assert_called_once()

    # Then
    assert cloned_segment.id != segment.id
    assert cloned_segment.uuid != segment.uuid
    assert cloned_segment.name == "Shallow Cloned Segment"
    assert cloned_segment.description == "New description"
    assert cloned_segment.project == segment.project
    assert cloned_segment.feature == segment.feature
    assert cloned_segment.version_of == segment
    assert cloned_segment.version is None
    assert cloned_segment.change_request == change_request

    # Shallow clone doesn't copy rules or metadata
    assert cloned_segment.rules.count() == 0
    assert cloned_segment.metadata.count() == 0


def test_clone(
    segment: Segment,
    required_a_segment_metadata_field: MetadataModelField,
) -> None:
    # Given
    parent_rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    child_rule = SegmentRule.objects.create(rule=parent_rule, type=SegmentRule.ANY_RULE)
    Condition.objects.create(
        rule=child_rule, property="test-property", operator=EQUAL, value="test-value"
    )

    segment_content_type = ContentType.objects.get_for_model(segment)
    metadata = Metadata.objects.create(
        object_id=segment.id,
        content_type=segment_content_type,
        model_field=required_a_segment_metadata_field,
        field_value="test-metadata",
    )

    # Initialize the service
    cloner = SegmentCloner(segment)

    # When
    cloned_segment = cloner.clone("Cloned Segment")

    # Then
    assert cloned_segment.id != segment.id
    assert cloned_segment.uuid != segment.uuid
    assert cloned_segment.name == "Cloned Segment"
    assert cloned_segment.description == segment.description
    assert cloned_segment.project == segment.project
    assert cloned_segment.feature == segment.feature
    assert cloned_segment.version_of == cloned_segment

    # Verify rules were cloned
    assert cloned_segment.rules.count() == segment.rules.count()
    cloned_parent_rule = cloned_segment.rules.first()
    assert cloned_parent_rule.type == parent_rule.type

    cloned_child_rule = cloned_parent_rule.rules.first()
    assert cloned_child_rule.type == child_rule.type

    cloned_condition = cloned_child_rule.conditions.first()
    assert cloned_condition.property == "test-property"
    assert cloned_condition.operator == EQUAL
    assert cloned_condition.value == "test-value"

    # Verify metadata was cloned
    assert cloned_segment.metadata.count() == segment.metadata.count()
    cloned_metadata = cloned_segment.metadata.first()
    assert cloned_metadata.model_field == metadata.model_field
    assert cloned_metadata.field_value == metadata.field_value
    assert cloned_metadata.id != metadata.id


def test_deep_clone(segment: Segment) -> None:
    # Given
    parent_rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    child_rule = SegmentRule.objects.create(rule=parent_rule, type=SegmentRule.ANY_RULE)
    Condition.objects.create(
        rule=child_rule, property="test-property", operator=EQUAL, value="test-value"
    )

    segment.version = 1
    original_version = segment.version
    segment.save()

    # Initialize the service
    cloner = SegmentCloner(segment)

    # When
    cloned_segment = cloner.deep_clone()

    # Then
    assert cloned_segment.id != segment.id
    assert cloned_segment.uuid != segment.uuid
    assert cloned_segment.name == segment.name
    assert cloned_segment.description == segment.description
    assert cloned_segment.project == segment.project
    assert cloned_segment.feature == segment.feature
    assert cloned_segment.version_of == segment

    segment.refresh_from_db()

    assert segment.version == original_version + 1

    assert cloned_segment.rules.count() == segment.rules.count()
    cloned_parent_rule = cloned_segment.rules.first()
    assert cloned_parent_rule.type == parent_rule.type

    cloned_child_rule = cloned_parent_rule.rules.first()
    assert cloned_child_rule.type == child_rule.type

    cloned_condition = cloned_child_rule.conditions.first()
    assert cloned_condition.property == "test-property"
    assert cloned_condition.operator == EQUAL
    assert cloned_condition.value == "test-value"

    # Verify metadata was NOT cloned (deep_clone doesn't clone metadata)
    assert cloned_segment.metadata.count() == 0


def test_clone_complex_segment_rules(project: Project, segment: Segment) -> None:
    """
    Test cloning a segment with a more complex rule structure:
    - Parent rule (ALL)
      - Child rule 1 (ANY)
        - 2 Conditions
      - Child rule 2 (NONE)
        - 1 Condition
    """
    # Given
    parent_rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)

    child_rule1 = SegmentRule.objects.create(
        rule=parent_rule, type=SegmentRule.ANY_RULE
    )
    Condition.objects.create(
        rule=child_rule1, property="email", operator=CONTAINS, value="@example.com"
    )
    Condition.objects.create(
        rule=child_rule1, property="age", operator=GREATER_THAN, value="21"
    )

    child_rule2 = SegmentRule.objects.create(
        rule=parent_rule, type=SegmentRule.NONE_RULE
    )
    Condition.objects.create(
        rule=child_rule2, property="country", operator=EQUAL, value="restricted"
    )

    cloner = SegmentCloner(segment)

    # When
    cloned_segment = cloner.clone("Complex Cloned Segment")

    # Then
    assert cloned_segment.id != segment.id
    assert cloned_segment.name == "Complex Cloned Segment"

    # Verify rules structure was cloned correctly
    assert cloned_segment.rules.count() == 1
    cloned_parent_rule = cloned_segment.rules.first()
    assert cloned_parent_rule.type == SegmentRule.ALL_RULE

    # Verify child rules
    assert cloned_parent_rule.rules.count() == 2

    # Get the child rules in a deterministic order
    cloned_child_rules = list(cloned_parent_rule.rules.all().order_by("type"))

    # Verify first child rule (ANY type)
    any_rule = next(
        rule for rule in cloned_child_rules if rule.type == SegmentRule.ANY_RULE
    )
    assert any_rule.conditions.count() == 2

    # Verify conditions of ANY rule
    condition_props = {cond.property: cond.value for cond in any_rule.conditions.all()}
    assert "email" in condition_props
    assert condition_props["email"] == "@example.com"
    assert "age" in condition_props
    assert condition_props["age"] == "21"

    # Verify second child rule (NONE type)
    none_rule = next(
        rule for rule in cloned_child_rules if rule.type == SegmentRule.NONE_RULE
    )
    assert none_rule.conditions.count() == 1

    # Verify condition of NONE rule
    none_condition = none_rule.conditions.first()
    assert none_condition.property == "country"
    assert none_condition.operator == EQUAL
    assert none_condition.value == "restricted"


def test_clone_raises_on_rule_clone_count_mismatch(segment: Segment) -> None:
    """Test that assertions are raised when rule cloning fails"""
    # Given
    SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)

    cloner = SegmentCloner(segment)

    with patch.object(SegmentRule, "deep_clone", return_value=None):
        # When/Then
        with pytest.raises(AssertionError, match="Mismatch during rule cloning"):
            cloner.clone("Error Segment")


def test_clone_error_on_metadata_count_mismatch(
    segment: Segment,
    required_a_segment_metadata_field: MetadataModelField,
) -> None:
    """Test that assertions are raised when metadata cloning fails"""
    # Given
    segment_content_type = ContentType.objects.get_for_model(segment)
    Metadata.objects.create(
        object_id=segment.id,
        content_type=segment_content_type,
        model_field=required_a_segment_metadata_field,
        field_value="test-metadata",
    )

    cloner = SegmentCloner(segment)

    with patch.object(Metadata, "deep_clone_for_new_entity", return_value=None):
        # When/Then - should raise assertion error because cloned_metadata will be empty
        with pytest.raises(AssertionError, match="Mismatch during metadata cloning"):
            cloner.clone("Error Segment")
