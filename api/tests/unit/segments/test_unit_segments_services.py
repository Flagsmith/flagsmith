from unittest.mock import patch

import pytest
from django.contrib.contenttypes.models import ContentType
from flag_engine.segments.constants import EQUAL, PERCENTAGE_SPLIT
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]

from features.models import Feature
from features.workflows.core.models import ChangeRequest
from metadata.models import Metadata, MetadataModelField
from projects.models import Project
from segments.models import Condition, Segment, SegmentRule
from segments.services import SegmentCloneService


def test_SegmentCloneService_shallow_clone(project: Project, segment: Segment) -> None:
    # Given
    cloner = SegmentCloneService(segment)
    change_request = ChangeRequest.objects.create(
        project=project, title="Test change request", user=None
    )

    # When
    cloned_segment = cloner.shallow_clone(
        name="Shallow Cloned Segment",
        description="New description",
        change_request=change_request,
    )

    # Then
    assert cloned_segment.history.count() == 1
    assert cloned_segment.id != segment.id
    assert cloned_segment.uuid != segment.uuid
    assert cloned_segment.name == "Shallow Cloned Segment"
    assert cloned_segment.description == "New description"
    assert cloned_segment.project == segment.project
    assert cloned_segment.feature == segment.feature
    assert cloned_segment.version_of == segment
    assert cloned_segment.version is None
    assert cloned_segment.change_request == change_request
    assert cloned_segment.rules.count() == 0
    assert cloned_segment.metadata.count() == 0


@pytest.mark.parametrize(
    "source_segment",
    [
        (lazy_fixture("segment")),
        (lazy_fixture("feature_specific_segment")),
    ],
)
def test_SegmentCloneService_clone_segment(
    project: Project,
    source_segment: Segment,
    required_a_segment_metadata_field: MetadataModelField,
) -> None:
    # Given
    cloner = SegmentCloneService(source_segment)
    new_segment_name = "cloned_segment"

    segment_rule = SegmentRule.objects.create(
        segment=source_segment,  # attach to source_segment instead of using fixture
        type=SegmentRule.ALL_RULE,
    )

    sub_rule = SegmentRule.objects.create(
        rule=segment_rule,
        type=SegmentRule.ALL_RULE,
    )

    created_condition = Condition.objects.create(
        rule=sub_rule,
        property="foo",
        operator=EQUAL,
        value="bar",
        created_with_segment=False,
    )

    # Preparing the metadata
    segment_content_type = ContentType.objects.get_for_model(source_segment)
    metadata = Metadata.objects.create(
        object_id=source_segment.id,
        content_type=segment_content_type,
        model_field=required_a_segment_metadata_field,
        field_value="test-clone-segment-metadata",
    )

    # When
    cloned_segment = cloner.clone(new_segment_name)
    # Then

    assert cloned_segment.name == new_segment_name
    assert cloned_segment.project == project
    assert cloned_segment.id != source_segment.id

    # Testing cloned segment main attributes
    assert cloned_segment.project_id == project.id
    assert cloned_segment.description == source_segment.description
    assert cloned_segment.version == 1
    assert cloned_segment.version_of_id == cloned_segment.id
    assert cloned_segment.change_request is None
    assert cloned_segment.feature_id == source_segment.feature_id

    # Testing cloning of rules
    assert cloned_segment.rules.count() == source_segment.rules.count()

    cloned_top_rule = cloned_segment.rules.first()
    assert cloned_top_rule is not None
    cloned_sub_rule = cloned_top_rule.rules.first()
    assert cloned_sub_rule is not None
    assert cloned_top_rule.type == segment_rule.type
    assert cloned_sub_rule.type == segment_rule.type

    # Testing cloning of sub-rules conditions
    cloned_condition = cloned_sub_rule.conditions.first()
    assert cloned_condition is not None
    assert cloned_condition.property == created_condition.property
    assert cloned_condition.operator == created_condition.operator
    assert cloned_condition.value == created_condition.value

    # Testing cloning of metadata
    cloned_metadata = cloned_segment.metadata.first()
    assert cloned_metadata.model_field == metadata.model_field
    assert cloned_metadata.field_value == metadata.field_value
    assert cloned_metadata.id != metadata.id


def test_SegmentCloneService_deep_clone_of_segment(
    project: Project,
    feature: Feature,
) -> None:
    # Given
    segment = Segment.objects.create(
        name="SpecialSegment",
        description="A lovely, special segment.",
        project=project,
        feature=feature,
    )

    # Check that the versioning is correct, since we'll be testing
    # against it later in the test.
    assert segment.version == 1
    assert segment.version_of == segment

    parent_rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)

    child_rule1 = SegmentRule.objects.create(
        rule=parent_rule, type=SegmentRule.ANY_RULE
    )
    child_rule2 = SegmentRule.objects.create(
        rule=parent_rule, type=SegmentRule.NONE_RULE
    )
    child_rule3 = SegmentRule.objects.create(
        rule=parent_rule, type=SegmentRule.NONE_RULE
    )
    child_rule4 = SegmentRule.objects.create(
        rule=parent_rule, type=SegmentRule.ANY_RULE
    )

    condition1 = Condition.objects.create(
        rule=child_rule1,
        property="child_rule1",
        operator=EQUAL,
        value="condition3",
        created_with_segment=True,
    )
    condition2 = Condition.objects.create(
        rule=child_rule2,
        property="child_rule2",
        operator=PERCENTAGE_SPLIT,
        value="0.2",
        created_with_segment=False,
    )
    condition3 = Condition.objects.create(
        rule=child_rule2,
        property="child_rule2",
        operator=EQUAL,
        value="condition5",
        created_with_segment=False,
    )

    condition4 = Condition.objects.create(
        rule=child_rule3,
        property="child_rule3",
        operator=EQUAL,
        value="condition6",
        created_with_segment=False,
    )

    condition5 = Condition.objects.create(
        rule=child_rule4,
        property="child_rule4",
        operator=EQUAL,
        value="condition7",
        created_with_segment=True,
    )

    # When
    cloned_segment = SegmentCloneService(segment).deep_clone()

    # Then
    assert cloned_segment.name == segment.name
    assert cloned_segment.description == segment.description
    assert cloned_segment.project == project
    assert cloned_segment.feature == feature
    assert cloned_segment.version == 1
    assert cloned_segment.version_of == segment

    assert segment.version == 2

    assert len(cloned_segment.rules.all()) == len(segment.rules.all()) == 1
    new_parent_rule = cloned_segment.rules.first()

    assert new_parent_rule is not None
    assert new_parent_rule.segment == cloned_segment
    assert new_parent_rule.type == parent_rule.type

    assert len(new_parent_rule.rules.all()) == len(parent_rule.rules.all()) == 4
    new_child_rule1, new_child_rule2, new_child_rule3, new_child_rule4 = list(
        new_parent_rule.rules.all()
    )

    assert new_child_rule1.type == child_rule1.type
    assert new_child_rule2.type == child_rule2.type
    assert new_child_rule3.type == child_rule3.type
    assert new_child_rule4.type == child_rule4.type

    assert (
        len(new_parent_rule.conditions.all()) == len(parent_rule.conditions.all()) == 0
    )

    assert (
        len(new_child_rule1.conditions.all()) == len(child_rule1.conditions.all()) == 1
    )
    new_condition1 = new_child_rule1.conditions.first()

    assert new_condition1 is not None
    assert new_condition1.property == condition1.property
    assert new_condition1.operator == condition1.operator
    assert new_condition1.value == condition1.value
    assert new_condition1.created_with_segment is condition1.created_with_segment

    assert (
        len(new_child_rule2.conditions.all()) == len(child_rule2.conditions.all()) == 2
    )
    new_condition2, new_condition3 = list(new_child_rule2.conditions.all())

    assert new_condition2 is not None
    assert new_condition2.property == condition2.property
    assert new_condition2.operator == condition2.operator
    assert new_condition2.value == condition2.value
    assert new_condition2.created_with_segment is condition2.created_with_segment

    assert new_condition3.property == condition3.property
    assert new_condition3.operator == condition3.operator
    assert new_condition3.value == condition3.value
    assert new_condition3.created_with_segment is condition3.created_with_segment

    assert (
        len(new_child_rule3.conditions.all()) == len(child_rule3.conditions.all()) == 1
    )
    new_condition4 = new_child_rule3.conditions.first()

    assert new_condition4 is not None
    assert new_condition4.property == condition4.property
    assert new_condition4.operator == condition4.operator
    assert new_condition4.value == condition4.value
    assert new_condition4.created_with_segment is condition4.created_with_segment

    assert (
        len(new_child_rule4.conditions.all()) == len(child_rule4.conditions.all()) == 1
    )
    new_condition5 = new_child_rule4.conditions.first()

    assert new_condition5 is not None
    assert new_condition5.property == condition5.property
    assert new_condition5.operator == condition5.operator
    assert new_condition5.value == condition5.value
    assert new_condition5.created_with_segment is condition5.created_with_segment


def test_SegmentCloneService_clone_raises_on_rule_clone_count_mismatch(
    segment: Segment,
) -> None:
    """Test that assertions are raised when rule cloning fails"""
    # Given
    SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)

    cloner = SegmentCloneService(segment)

    with patch.object(SegmentRule, "deep_clone", return_value=None):
        # When/Then
        with pytest.raises(AssertionError, match="Mismatch during rule cloning"):
            cloner.clone("Error Segment")


def test_SegmentCloneService_clone_error_on_metadata_count_mismatch(
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

    cloner = SegmentCloneService(segment)

    with patch.object(Metadata, "deep_clone_for_new_entity", return_value=None):
        # When/Then
        with pytest.raises(AssertionError, match="Mismatch during metadata cloning"):
            cloner.clone("Error Segment")


def test_SegmentCloneService_deep_clone_of_segment_with_improper_sub_rule(
    project: Project,
    feature: Feature,
) -> None:
    # Given
    segment = Segment.objects.create(
        name="SpecialSegment",
        description="A lovely, special segment.",
        project=project,
        feature=feature,
    )

    rule = SegmentRule.objects.create(
        type=SegmentRule.ALL_RULE,
        segment=segment,
    )

    # Rule with invalid relation to both segment and rule.
    SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE, rule=rule)

    with pytest.raises(AssertionError) as exception:
        SegmentCloneService(segment).deep_clone()

    assert (
        "AssertionError: Unexpected rule, expecting segment set not rule"
        == exception.exconly()
    )


def test_SegmentCloneService_deep_clone_of_segment_with_grandchild_rule(
    project: Project,
    feature: Feature,
) -> None:
    # Given
    segment = Segment.objects.create(
        name="SpecialSegment",
        description="A lovely, special segment.",
        project=project,
        feature=feature,
    )

    parent_rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)

    child_rule = SegmentRule.objects.create(rule=parent_rule, type=SegmentRule.ANY_RULE)

    # Grandchild rule, which is invalid
    SegmentRule.objects.create(rule=child_rule, type=SegmentRule.ANY_RULE)

    with pytest.raises(AssertionError) as exception:
        SegmentCloneService(segment).deep_clone()

    assert (
        "AssertionError: Expected two layers of rules, not more" == exception.exconly()
    )
