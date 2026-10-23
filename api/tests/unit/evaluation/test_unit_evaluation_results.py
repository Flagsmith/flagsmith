import pytest

from evaluation.results import get_split_weight
from evaluation.types import FlagResult


@pytest.mark.parametrize(
    "reason, expected_weight",
    [
        pytest.param("SPLIT; weight=30", 30.0, id="split"),
        pytest.param(
            "SPLIT; weight=33.333333333333336",
            33.333333333333336,
            id="split_fractional_weight",
        ),
        pytest.param("DEFAULT", None, id="default"),
        pytest.param("TARGETING_MATCH; segment=beta", None, id="segment_override"),
        pytest.param(
            "TARGETING_MATCH; segment=x; SPLIT; weight=5",
            None,
            id="segment_override_named_like_split",
        ),
    ],
)
def test_get_split_weight__reason__returns_expected_weight(
    reason: str,
    expected_weight: float | None,
) -> None:
    # Given
    flag_result: FlagResult = {
        "name": "feature",
        "enabled": True,
        "value": "value",
        "reason": reason,
        "variant": None,
    }

    # When
    weight = get_split_weight(flag_result)

    # Then
    assert weight == expected_weight
