import pytest

from features.dependencies.mappers import map_rules_to_prerequisite_feature_names
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
