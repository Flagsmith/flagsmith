from unittest.mock import mock_open, patch

from task_processor.thread_monitoring import (
    THREAD_COUNTS_FILE_PATH,
    ThreadCounts,
    get_thread_counts,
    write_thread_counts,
)


def test_write_thread_counts() -> None:
    # Given
    thread_counts = ThreadCounts(running=1, expected=1)

    # When
    with patch("builtins.open", mock_open()) as mocked_open:
        write_thread_counts(thread_counts)

    # Then
    mocked_open.assert_called_once_with(THREAD_COUNTS_FILE_PATH, "w+")
    mocked_open.return_value.write.assert_called_once_with(thread_counts.json())


def test_get_thread_counts() -> None:
    # Given
    data = '{"running": 1, "expected": 2}'

    # When
    with patch("builtins.open", mock_open(read_data=data)) as mocked_open:
        thread_counts = get_thread_counts()

    # Then
    mocked_open.assert_called_once_with(THREAD_COUNTS_FILE_PATH, "r")

    assert thread_counts.running == 1
    assert thread_counts.expected == 2
