import pytest

from features.versioning.dataclasses import Conflict


@pytest.mark.parametrize("segment_id, expected_result", ((None, True), (1, False)))
def test_conflict_is_environment_default(
    segment_id: int | None, expected_result: bool
) -> None:
    assert Conflict(segment_id=segment_id).is_environment_default is expected_result
