import pytest

from environments.identities.traits.models import Trait
from segments.models import (
    EQUAL,
    GREATER_THAN,
    GREATER_THAN_INCLUSIVE,
    LESS_THAN,
    LESS_THAN_INCLUSIVE,
    NOT_EQUAL,
    Condition,
)


@pytest.mark.parametrize(
    "operator, trait_value, condition_value, result",
    [
        (EQUAL, "1.0.0", "1.0.0", True),
        (EQUAL, "1.0.0", "1.0.1", False),
        (NOT_EQUAL, "1.0.0", "1.0.0", False),
        (NOT_EQUAL, "1.0.0", "1.0.1", True),
        (GREATER_THAN, "1.0.1", "1.0.0", True),
        (GREATER_THAN, "1.0.0", "1.0.0-beta", True),
        (GREATER_THAN, "1.0.1", "1.2.0", False),
        (GREATER_THAN, "1.0.1", "1.0.1", False),
        (GREATER_THAN, "1.2.4", "1.2.3-pre.2+build.4", True),
        (LESS_THAN, "1.0.0", "1.0.1", True),
        (LESS_THAN, "1.0.0", "1.0.0", False),
        (LESS_THAN, "1.0.1", "1.0.0", False),
        (LESS_THAN, "1.0.0-rc.2", "1.0.0-rc.3", True),
        (GREATER_THAN_INCLUSIVE, "1.0.1", "1.0.0", True),
        (GREATER_THAN_INCLUSIVE, "1.0.1", "1.2.0", False),
        (GREATER_THAN_INCLUSIVE, "1.0.1", "1.0.1", True),
        (LESS_THAN_INCLUSIVE, "1.0.0", "1.0.1", True),
        (LESS_THAN_INCLUSIVE, "1.0.0", "1.0.0", True),
        (LESS_THAN_INCLUSIVE, "1.0.1", "1.0.0", False),
    ],
)
def test_does_identity_match_for_semver_values(
    identity, operator, trait_value, condition_value, result
):
    # Given
    condition = Condition(operator=operator, property="version", value=condition_value)
    traits = [
        Trait(
            trait_key="version",
            string_value=trait_value,
            identity=identity,
        )
    ]
    # Then
    assert condition.does_identity_match(identity, traits) is result
