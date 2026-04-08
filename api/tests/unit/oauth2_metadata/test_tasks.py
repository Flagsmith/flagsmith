from unittest.mock import MagicMock

from oauth2_metadata.tasks import clear_expired_oauth2_tokens


def test_clear_expired_oauth2_tokens__called__invokes_cleartokens_command(
    mocker: MagicMock,
) -> None:
    # Given
    mock_call_command = mocker.patch("oauth2_metadata.tasks.call_command")

    # When
    clear_expired_oauth2_tokens()

    # Then
    mock_call_command.assert_called_once_with("cleartokens")
