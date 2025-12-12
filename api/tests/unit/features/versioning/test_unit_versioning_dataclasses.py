from unittest.mock import Mock

import pytest

from core.dataclasses import AuthorData
from features.versioning.dataclasses import Conflict


@pytest.mark.parametrize("segment_id, expected_result", ((None, True), (1, False)))
def test_conflict_is_environment_default(
    segment_id: int | None, expected_result: bool
) -> None:
    assert Conflict(segment_id=segment_id).is_environment_default is expected_result


def test_author_data_from_request_sets_api_key_for_non_user() -> None:
    mock_master_api_key = Mock(spec_set=["id", "name"])
    mock_api_key_user = Mock()
    mock_api_key_user.key = mock_master_api_key
    mock_request = Mock()
    mock_request.user = mock_api_key_user

    author = AuthorData.from_request(mock_request)

    assert author.api_key is mock_master_api_key
    assert author.user is None


def test_author_data_from_request_raises_for_invalid_user() -> None:
    mock_request = Mock()
    mock_request.user = object()  # No .key attribute

    with pytest.raises(ValueError) as exc_info:
        AuthorData.from_request(mock_request)

    assert "must be FFAdminUser or have an API key" in str(exc_info.value)
