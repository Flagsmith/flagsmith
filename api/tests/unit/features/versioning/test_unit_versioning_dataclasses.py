from unittest.mock import Mock

import pytest

from features.versioning.dataclasses import Conflict, FlagChangeSet


@pytest.mark.parametrize("segment_id, expected_result", ((None, True), (1, False)))
def test_conflict_is_environment_default(
    segment_id: int | None, expected_result: bool
) -> None:
    assert Conflict(segment_id=segment_id).is_environment_default is expected_result


def test_set_audit_fields_from_request_sets_api_key_for_non_user() -> None:
    mock_api_key = Mock()
    mock_api_key.key = "test_api_key"
    mock_request = Mock()
    mock_request.user = mock_api_key

    change_set = FlagChangeSet(
        enabled=True,
        feature_state_value="test",
        type_="string",
    )
    change_set.set_audit_fields_from_request(mock_request)

    assert change_set.api_key == "test_api_key"
    assert change_set.user is None


def test_set_audit_fields_from_request_raises_for_invalid_user() -> None:
    mock_request = Mock()
    mock_request.user = object()  # No .key attribute

    change_set = FlagChangeSet(
        enabled=True,
        feature_state_value="test",
        type_="string",
    )

    with pytest.raises(ValueError) as exc_info:
        change_set.set_audit_fields_from_request(mock_request)

    assert "must be FFAdminUser or have an API key" in str(exc_info.value)
