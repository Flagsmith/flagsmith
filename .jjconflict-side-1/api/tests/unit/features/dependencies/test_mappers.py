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


@pytest.mark.parametrize(
    "segment, environment_defaults, expected_value_source",
    [
        pytest.param(
            Segment(feature_id=1, managed_by=SegmentManagedBy.DEPENDENCY),
            {1: FeatureState(id=1, feature_id=1)},
            FeatureState(id=1, feature_id=1),
            id="dependency_segment__environment_default",
        ),
        pytest.param(
            Segment(feature_id=1, managed_by=SegmentManagedBy.DEPENDENCY),
            {},
            FeatureState(id=2, feature_id=1),
            id="dependency_segment_without_environment_default__override",
        ),
        pytest.param(
            Segment(feature_id=None),
            {1: FeatureState(id=1, feature_id=1)},
            FeatureState(id=2, feature_id=1),
            id="user_segment__override",
        ),
        pytest.param(
            Segment(feature_id=1, managed_by=SegmentManagedBy.EXPERIMENT),
            {1: FeatureState(id=1, feature_id=1)},
            FeatureState(id=2, feature_id=1),
            id="experiment_segment__override",
        ),
        pytest.param(
            Segment(feature_id=1, managed_by=SegmentManagedBy.RELEASE_PIPELINE),
            {1: FeatureState(id=1, feature_id=1)},
            FeatureState(id=2, feature_id=1),
            id="release_pipeline_segment__override",
        ),
    ],
)
def test_map_override_to_value_source__segment_override__returns_expected_value_source(
    segment: Segment,
    environment_defaults: dict[int, FeatureState],
    expected_value_source: FeatureState,
) -> None:
    # Given / When
    value_source = map_override_to_value_source(
        FeatureState(id=2, feature_id=1),
        segment=segment,
        environment_defaults=environment_defaults,
    )

    # Then
    assert value_source == expected_value_source
