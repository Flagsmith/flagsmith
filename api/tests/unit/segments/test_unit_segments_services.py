import pytest
from django.contrib.contenttypes.models import ContentType
from flag_engine.segments.constants import EQUAL, PERCENTAGE_SPLIT
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]
from pytest_mock import MockerFixture

from features.models import Feature
from features.workflows.core.models import ChangeRequest
from metadata.models import Metadata, MetadataModelField
from projects.models import Project
from segments.models import Condition, Segment, SegmentRule
from segments.services import SegmentCloneService


# TODO: Remove because this is testing a function that is only used in tests.
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
        lazy_fixture("segment"),
        lazy_fixture("feature_specific_segment"),
    ],
)
def test_SegmentCloneService_clone__creates_full_standalone_copy_of_segment(
    project: Project,
    required_a_segment_metadata_field: MetadataModelField,
    source_segment: Segment,
) -> None:
    # Given
    original_top_rule = SegmentRule.objects.create(
        segment=source_segment,
        type=SegmentRule.ALL_RULE,
    )

    original_sub_rule = SegmentRule.objects.create(
        rule=original_top_rule,
        type=SegmentRule.ALL_RULE,
    )

    original_condition = Condition.objects.create(
        rule=original_sub_rule,
        property="foo",
        operator=EQUAL,
        value="bar",
        created_with_segment=False,
    )

    segment_content_type = ContentType.objects.get_for_model(source_segment)
    original_metadata = Metadata.objects.create(
        object_id=source_segment.id,
        content_type=segment_content_type,
        model_field=required_a_segment_metadata_field,
        field_value="test-clone-segment-metadata",
    )

    # When
    service = SegmentCloneService(source_segment)
    cloned_segment = service.clone("cloned-segment")

    # Then
    assert cloned_segment.pk != source_segment.pk
    assert cloned_segment.name == "cloned-segment"
    assert cloned_segment.project == project
    assert cloned_segment.project_id == project.pk
    assert cloned_segment.description == source_segment.description
    assert cloned_segment.version == 1
    assert cloned_segment.version_of_id == cloned_segment.pk
    assert cloned_segment.change_request is None
    assert cloned_segment.feature_id == source_segment.feature_id

    cloned_top_rule = cloned_segment.rules.get()
    assert cloned_top_rule.pk != original_top_rule.pk
    assert cloned_top_rule.type == original_top_rule.type
    cloned_sub_rule = cloned_top_rule.rules.get()
    assert cloned_sub_rule.pk != original_sub_rule.pk
    assert cloned_sub_rule.type == original_sub_rule.type

    cloned_condition = cloned_sub_rule.conditions.get()
    assert cloned_condition.pk != original_condition.pk
    assert cloned_condition.property == original_condition.property
    assert cloned_condition.operator == original_condition.operator
    assert cloned_condition.value == original_condition.value

    cloned_metadata = cloned_segment.metadata.get()
    assert cloned_metadata.pk != original_metadata.pk
    assert cloned_metadata.model_field == original_metadata.model_field
    assert cloned_metadata.field_value == original_metadata.field_value


def test_SegmentCloneService_deep_clone__creates_historical_version_of_segment(
    feature: Feature,
    project: Project,
) -> None:
    # Given
    original_segment = Segment.objects.create(
        name="SpecialSegment",
        description="A lovely, special segment.",
        project=project,
        feature=feature,
    )
    assert original_segment.version == 1
    assert original_segment.version_of == original_segment

    original_top_rule = SegmentRule.objects.create(
        segment=original_segment,
        type=SegmentRule.ALL_RULE,
    )

    original_sub_rule1 = SegmentRule.objects.create(
        rule=original_top_rule,
        type=SegmentRule.ANY_RULE,
    )
    original_sub_rule2 = SegmentRule.objects.create(
        rule=original_top_rule,
        type=SegmentRule.NONE_RULE,
    )

    original_condition1 = Condition.objects.create(
        rule=original_sub_rule1,
        property="condition1-property",
        operator=EQUAL,
        value="condition1-value",
        created_with_segment=True,
    )
    original_condition2 = Condition.objects.create(
        rule=original_sub_rule2,
        property="condition2-property",
        operator=PERCENTAGE_SPLIT,
        value="condition2-value",
        created_with_segment=False,
    )
    original_condition3 = Condition.objects.create(
        rule=original_sub_rule2,
        property="condition3-property",
        operator=EQUAL,
        value="condition3-value",
        created_with_segment=False,
    )

    # When
    service = SegmentCloneService(original_segment)
    cloned_segment = service.deep_clone()

    # Then
    original_segment.refresh_from_db()
    assert original_segment.version == 2

    assert cloned_segment.pk != original_segment.pk
    assert cloned_segment.name == original_segment.name
    assert cloned_segment.description == original_segment.description
    assert cloned_segment.project == project
    assert cloned_segment.feature == feature
    assert cloned_segment.version == 1
    assert cloned_segment.version_of == original_segment

    cloned_top_rule = cloned_segment.rules.get()
    assert cloned_top_rule.pk != original_top_rule.pk
    assert cloned_top_rule.segment == cloned_segment
    assert cloned_top_rule.type == original_top_rule.type

    cloned_sub_rules = list(cloned_top_rule.rules.all())
    assert len(cloned_sub_rules) == 2
    assert cloned_sub_rules[0].pk != original_sub_rule1.pk
    assert cloned_sub_rules[0].type == original_sub_rule1.type
    assert cloned_sub_rules[1].pk != original_sub_rule2.pk
    assert cloned_sub_rules[1].type == original_sub_rule2.type

    cloned_conditions1 = list(cloned_sub_rules[0].conditions.all())
    assert len(cloned_conditions1) == 1
    assert cloned_conditions1[0].pk != original_condition1.pk
    assert cloned_conditions1[0].property == original_condition1.property
    assert cloned_conditions1[0].operator == original_condition1.operator
    assert cloned_conditions1[0].value == original_condition1.value
    assert cloned_conditions1[0].created_with_segment is True

    cloned_conditions2 = list(cloned_sub_rules[1].conditions.all())
    assert len(cloned_conditions2) == 2
    assert cloned_conditions2[0].pk != original_condition2.pk
    assert cloned_conditions2[0].property == original_condition2.property
    assert cloned_conditions2[0].operator == original_condition2.operator
    assert cloned_conditions2[0].value == original_condition2.value
    assert cloned_conditions2[0].created_with_segment is False
    assert cloned_conditions2[1].pk != original_condition3.pk
    assert cloned_conditions2[1].property == original_condition3.property
    assert cloned_conditions2[1].operator == original_condition3.operator
    assert cloned_conditions2[1].value == original_condition3.value
    assert cloned_conditions2[1].created_with_segment is False


def test_SegmentCloneService_clone__raises_when_cloned_rules_count_mismatches(
    mocker: MockerFixture,
    segment: Segment,
) -> None:
    # Given
    SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    mocker.patch.object(SegmentRule, "deep_clone", return_value=None)

    # When/Then
    service = SegmentCloneService(segment)
    with pytest.raises(AssertionError, match="Mismatch during rule cloning"):
        service.clone("Error Segment")


def test_SegmentCloneService_clone__raises_when_cloned_metadata_count_mismatches(
    mocker: MockerFixture,
    segment: Segment,
    required_a_segment_metadata_field: MetadataModelField,
) -> None:
    # Given
    segment_content_type = ContentType.objects.get_for_model(segment)
    Metadata.objects.create(
        object_id=segment.id,
        content_type=segment_content_type,
        model_field=required_a_segment_metadata_field,
        field_value="test-metadata",
    )
    mocker.patch.object(Metadata, "deep_clone_for_new_entity", return_value=None)

    # When/Then
    service = SegmentCloneService(segment)
    error_message = "Mismatch during metadata cloning"
    with pytest.raises(AssertionError, match=error_message):
        service.clone("Error Segment")


def test_SegmentCloneService_deep_clone__raises_when_theres_an_invalid_rule(
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

    SegmentRule.objects.create(  # Invalid relation to both segment and rule
        rule=rule,
        segment=segment,
        type=SegmentRule.ALL_RULE,
    )

    # When/Then
    error_message = "Unexpected rule, expecting segment set not rule"
    with pytest.raises(AssertionError, match=error_message):
        SegmentCloneService(segment).deep_clone()


def test_SegmentCloneService_deep_clone__raises_when_rules_are_nested_too_deep(
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

    top_rule = SegmentRule.objects.create(
        segment=segment,
        type=SegmentRule.ALL_RULE,
    )

    sub_rule = SegmentRule.objects.create(
        rule=top_rule,
        type=SegmentRule.ANY_RULE,
    )

    SegmentRule.objects.create(  # Grandchild rule
        rule=sub_rule,
        type=SegmentRule.ANY_RULE,
    )

    # When/Then
    error_message = "Expected two layers of rules, not more"
    with pytest.raises(AssertionError, match=error_message):
        SegmentCloneService(segment).deep_clone()
