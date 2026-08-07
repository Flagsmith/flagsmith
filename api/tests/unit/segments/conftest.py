import pytest
from django.conf import settings
from pytest import FixtureRequest

from tests.types import InvalidSegmentRulesCase


@pytest.fixture(
    params=[
        pytest.param(
            (
                lambda rules: rules.clear(),
                {"rules": {"non_field_errors": ["This list may not be empty."]}},
            ),
            id="no-rules-provided",
        ),
        pytest.param(
            (
                lambda rules: rules[0]["conditions"].extend(
                    {"property": f"prop_{i}", "operator": "EQUAL", "value": "red"}
                    for i in range(settings.SEGMENT_RULES_CONDITIONS_LIMIT)
                ),
                {
                    "segment": [
                        f"The segment has {settings.SEGMENT_RULES_CONDITIONS_LIMIT + 3} conditions, "
                        f"which exceeds the maximum condition count of {settings.SEGMENT_RULES_CONDITIONS_LIMIT}."
                    ]
                },
            ),
            id="condition-count-over-limit",
        ),
        pytest.param(
            (
                lambda rules: rules[0]["conditions"][0].update(
                    value="x" * (settings.SEGMENT_CONDITION_VALUE_LIMIT + 1)
                ),
                {
                    "rules": [
                        {
                            "conditions": [
                                {
                                    "value": [
                                        f"Ensure this field has no more than "
                                        f"{settings.SEGMENT_CONDITION_VALUE_LIMIT} characters."
                                    ]
                                }
                            ]
                        }
                    ]
                },
            ),
            id="condition-value-over-length-limit",
        ),
        pytest.param(
            (
                lambda rules: rules[0]["rules"][0].update(
                    rules=[
                        {
                            "type": "ANY",
                            "conditions": [
                                {
                                    "property": "too",
                                    "operator": "EQUAL",
                                    "value": "deep",
                                },
                            ],
                        },
                    ],
                ),
                {"segment": ["Rules must not be nested more than 2 levels deep."]},
            ),
            id="rules-nested-too-deep",
        ),
    ],
)
def invalid_rules_case(request: FixtureRequest) -> InvalidSegmentRulesCase:
    return request.param  # type: ignore[no-any-return]
