from unittest.mock import Mock

import pytest

from core.dataclasses import AuthorData
from features.versioning.dataclasses import Conflict


@pytest.mark.parametrize("segment_id, expected_result", ((None, True), (1, False)))
def test_conflict__given_segment_id__returns_expected_is_environment_default(
    segment_id: int | None, expected_result: bool
) -> None:
    # Given
    conflict = Conflict(segment_id=segment_id)
    # When / Then
    assert conflict.is_environment_default is expected_result


def test_author_data_from_request__api_key_user__sets_api_key() -> None:
    # Given
    mock_master_api_key = Mock(spec_set=["id", "name"])
    mock_api_key_user = Mock()
    mock_api_key_user.key = mock_master_api_key
    mock_request = Mock()
    mock_request.user = mock_api_key_user

    # When
    author = AuthorData.from_request(mock_request)

    # Then
    assert author.api_key is mock_master_api_key
    assert author.user is None


def test_author_data_from_request__invalid_user__raises_value_error() -> None:
    # Given
    mock_request = Mock()
    mock_request.user = object()  # No .key attribute

    # When / Then
    with pytest.raises(ValueError) as exc_info:
        AuthorData.from_request(mock_request)

    assert "must be FFAdminUser or have an API key" in str(exc_info.value)
