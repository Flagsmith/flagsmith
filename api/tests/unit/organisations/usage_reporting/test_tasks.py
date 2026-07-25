from pytest_mock import MockerFixture

from organisations.tasks import push_usage_to_control_plane


def test_push_usage_to_control_plane__called__delegates_to_service(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_push = mocker.patch("organisations.tasks.push_usage_snapshots")

    # When
    push_usage_to_control_plane()

    # Then
    assert mock_push.call_args_list == [mocker.call()]
