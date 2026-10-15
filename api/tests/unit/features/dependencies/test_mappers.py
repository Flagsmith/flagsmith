import pytest

from features.dependencies.mappers import (
    map_override_to_value_source,
    map_rules_to_prerequisite_feature_names,
)
from features.models import FeatureState
from segments.models import Segment, SegmentManagedBy
from segments.types import SegmentRule


@pytest.mark.parametrize(
    "condition_property",
    [
        "$.flags['unterminated",
        "$.flags['flag_a','flag_b'].enabled",
        "$.flags..enabled",
        "$.traits.flags.enabled",
        "$.flagsmith.enabled",
        "$.flags",
    ],
)
def test_map_rules_to_prerequisite_feature_names__invalid_prerequisite_jsonpath__ignores_property(
    condition_property: str,
) -> None:
    # Given
    rules: list[SegmentRule] = [
        {
            "type": "ALL",
            "conditions": [
                {
                    "property": condition_property,
                    "operator": "EQUAL",
                    "value": "true",
                    "description": None,
                }
            ],
        }
    ]

    # When
    feature_names_by_json_path = map_rules_to_prerequisite_feature_names(rules)

    # Then
    assert feature_names_by_json_path == {}


def test_map_override_to_value_source__dependency_override__returns_environment_default() -> (
    None
):
    # Given
    override = FeatureState(id=2, feature_id=1)
    environment_default = FeatureState(id=1, feature_id=1)

    # When
    value_source = map_override_to_value_source(
        override,
        segment=Segment(feature_id=1, managed_by=SegmentManagedBy.DEPENDENCY),
        environment_defaults={1: environment_default},
    )

    # Then
    assert value_source is environment_default


@pytest.mark.parametrize(
    "segment",
    [
        pytest.param(Segment(feature_id=None), id="user_segment"),
        pytest.param(
            Segment(feature_id=1, managed_by=SegmentManagedBy.EXPERIMENT),
            id="experiment",
        ),
        pytest.param(
            Segment(feature_id=1, managed_by=SegmentManagedBy.RELEASE_PIPELINE),
            id="release_pipeline",
        ),
        pytest.param(
            Segment(feature_id=3, managed_by=SegmentManagedBy.DEPENDENCY),
            id="another_feature_dependency",
        ),
    ],
)
def test_map_override_to_value_source__not_dependency_override__returns_override(
    segment: Segment,
) -> None:
    # Given
    override = FeatureState(id=2, feature_id=1)

    # When
    value_source = map_override_to_value_source(
        override,
        segment=segment,
        environment_defaults={1: FeatureState(id=1, feature_id=1)},
    )

    # Then
    assert value_source is override


def test_map_override_to_value_source__environment_default_missing__returns_override() -> (
    None
):
    # Given
    override = FeatureState(id=2, feature_id=1)

    # When
    value_source = map_override_to_value_source(
        override,
        segment=Segment(feature_id=1, managed_by=SegmentManagedBy.DEPENDENCY),
        environment_defaults={},
    )

    # Then
    assert value_source is override
