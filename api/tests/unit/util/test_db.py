import pytest
from django.db import OperationalError, connection
from pytest_mock import MockerFixture

from core.exceptions import StatementTimeoutError
from util.db import closing_stale_connections, with_statement_timeout


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


@pytest.mark.django_db
def test_with_statement_timeout__slow_query__raises_statement_timeout_error() -> None:
    # Given
    cursor = connection.cursor()

    # When
    with pytest.raises(StatementTimeoutError):
        with with_statement_timeout(milliseconds=1):
            cursor.execute("SELECT pg_sleep(0.1)")

    # Then
    cursor.execute("SELECT 1")
    assert cursor.fetchone() == (1,)


@pytest.mark.django_db
def test_with_statement_timeout__other_database_error__propagates_error() -> None:
    # Given
    error = OperationalError("connection lost")

    # When
    with pytest.raises(OperationalError) as exc_info:
        with with_statement_timeout(milliseconds=1000):
            raise error

    # Then
    assert exc_info.value is error
