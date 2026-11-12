from pytest_mock import MockerFixture

from telemetry.tasks import push_usage


def test_push_usage__called__pushes_usage_snapshots(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_push_usage_snapshots = mocker.patch("telemetry.tasks.push_usage_snapshots")

    # When
    push_usage()

    # Then
    mock_push_usage_snapshots.assert_called_once_with()
