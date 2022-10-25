import pytest

from sse.decorators import generate_identity_update_message
from sse.exceptions import ViewResponseDoesNotHaveStatus


def test_generate_identity_update_message_decorator_make_correct_call(
    mocker, environment
):
    # Given
    identifier = "identifier"
    request = mocker.MagicMock(
        environment=environment, data={"identity": {"identifier": identifier}}
    )
    response = mocker.MagicMock(status_code=200)
    mocked_send_identity_update_message = mocker.patch(
        "sse.decorators.send_identity_update_message", autospec=True
    )

    @generate_identity_update_message()
    def a_view_function(request, *args, **kwargs):
        return response

    # When
    _ = a_view_function(request)

    # Then
    mocked_send_identity_update_message.assert_called_once_with(environment, identifier)


def test_generate_identity_update_message_raises_exception_if_response_does_not_have_status(
    mocker, environment
):
    # Given
    request = mocker.MagicMock(environment=environment)

    @generate_identity_update_message()
    def a_view_function(request, *args, **kwargs):
        return None

    # When
    with pytest.raises(ViewResponseDoesNotHaveStatus):
        _ = a_view_function(request)
