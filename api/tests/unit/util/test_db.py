from pytest_mock import MockerFixture

from util.db import closing_stale_connections


def test_closing_stale_connections__exit__calls_close_old_connections(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_close_old_connections = mocker.patch("util.db.close_old_connections")

    # When
    with closing_stale_connections():
        pass

    # Then
    mock_close_old_connections.assert_called_once_with()
