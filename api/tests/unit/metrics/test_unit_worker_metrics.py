from pathlib import Path

import pytest

from metrics import worker_metrics

class MockGaugeLabels:
    def __init__(self):
        self.set_called_with = None

    def set(self, value):
        self.set_called_with = value


class MockGauge:
    def __init__(self):
        self.labels_called_with = None
        self.remove_called_with = None
        self.mock_labels = MockGaugeLabels()
        self.should_raise_on_remove = None

    def labels(self, *, pid):
        self.labels_called_with = pid
        return self.mock_labels

    def remove(self, *, pid):
        self.remove_called_with = pid
        if self.should_raise_on_remove:
            raise self.should_raise_on_remove


class UnreadableStatusPath:
    def read_text(self, encoding: str) -> str:
        raise OSError("status file unavailable")


def test_get_current_process_max_rss_bytes__vmhwm_available__returns_bytes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Given
    max_rss_kb = 123
    status_path = tmp_path / "status"
    status_path.write_text(
        f"Name:\tgunicorn\nVmHWM:\t{max_rss_kb} kB\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(worker_metrics, "PROC_SELF_STATUS_PATH", status_path)

    # When
    result = worker_metrics.get_current_process_max_rss_bytes()

    # Then
    assert result == max_rss_kb * worker_metrics.MAX_RSS_KB_TO_BYTES


def test_get_current_process_max_rss_bytes__vmhwm_has_extra_whitespace__returns_bytes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Given
    max_rss_kb = 456
    status_path = tmp_path / "status"
    status_path.write_text(
        f"Name:\tgunicorn\n  VmHWM:   {max_rss_kb}   kB  \nVmRSS:\t10 kB\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(worker_metrics, "PROC_SELF_STATUS_PATH", status_path)

    # When
    result = worker_metrics.get_current_process_max_rss_bytes()

    # Then
    assert result == max_rss_kb * worker_metrics.MAX_RSS_KB_TO_BYTES


def test_get_current_process_max_rss_bytes__status_file_missing__returns_none(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Given
    monkeypatch.setattr(worker_metrics, "PROC_SELF_STATUS_PATH", tmp_path / "missing")

    # When
    result = worker_metrics.get_current_process_max_rss_bytes()

    # Then
    assert result is None


def test_get_current_process_max_rss_bytes__vmhwm_missing__returns_none(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Given
    status_path = tmp_path / "status"
    status_path.write_text("Name:\tgunicorn\nVmRSS:\t10 kB\n", encoding="utf-8")
    monkeypatch.setattr(worker_metrics, "PROC_SELF_STATUS_PATH", status_path)

    # When
    result = worker_metrics.get_current_process_max_rss_bytes()

    # Then
    assert result is None


@pytest.mark.parametrize(
    "vmhwm_value",
    [
        "-1 kB",
        "not-a-number kB",
        "123 MB",
        "123",
        "123 kB extra",
    ],
)
def test_get_current_process_max_rss_bytes__vmhwm_invalid__returns_none(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    vmhwm_value: str,
) -> None:
    # Given
    status_path = tmp_path / "status"
    status_path.write_text(
        f"Name:\tgunicorn\nVmHWM:\t{vmhwm_value}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(worker_metrics, "PROC_SELF_STATUS_PATH", status_path)

    # When
    result = worker_metrics.get_current_process_max_rss_bytes()

    # Then
    assert result is None


def test_get_current_process_max_rss_bytes__status_file_read_error__returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.setattr(worker_metrics, "PROC_SELF_STATUS_PATH", UnreadableStatusPath())

    # When
    result = worker_metrics.get_current_process_max_rss_bytes()

    # Then
    assert result is None

def test_update_worker_metrics__rss_available__updates_gauge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    mock_rss = 1048576  # 1 MB
    mock_pid = 12345
    mock_gauge = MockGauge()

    monkeypatch.setattr(worker_metrics, "get_current_process_max_rss_bytes", lambda: mock_rss)
    monkeypatch.setattr(worker_metrics.os, "getpid", lambda: mock_pid)
    monkeypatch.setattr(worker_metrics, "flagsmith_worker_rss_bytes", mock_gauge)

    # When
    worker_metrics.update_worker_metrics()

    # Then
    assert mock_gauge.labels_called_with == str(mock_pid)
    assert mock_gauge.mock_labels.set_called_with == mock_rss

def test_update_worker_metrics__rss_none__does_not_update_gauge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    mock_pid = 12345
    mock_gauge = MockGauge()

    monkeypatch.setattr(worker_metrics, "get_current_process_max_rss_bytes", lambda: None)
    monkeypatch.setattr(worker_metrics.os, "getpid", lambda: mock_pid)
    monkeypatch.setattr(worker_metrics, "flagsmith_worker_rss_bytes", mock_gauge)

    # When
    worker_metrics.update_worker_metrics()

    # Then
    assert mock_gauge.labels_called_with is None

def test_clear_worker_metrics__removes_gauge_label(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    mock_pid = 67890
    mock_gauge = MockGauge()

    monkeypatch.setattr(worker_metrics.os, "getpid", lambda: mock_pid)
    monkeypatch.setattr(worker_metrics, "flagsmith_worker_rss_bytes", mock_gauge)

    # When
    worker_metrics.clear_worker_metrics()

    # Then
    assert mock_gauge.remove_called_with == str(mock_pid)


def test_clear_worker_metrics__keyerror__silently_handles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    mock_pid = 67890
    mock_gauge = MockGauge()
    mock_gauge.should_raise_on_remove = KeyError("Label not found")

    monkeypatch.setattr(worker_metrics.os, "getpid", lambda: mock_pid)
    monkeypatch.setattr(worker_metrics, "flagsmith_worker_rss_bytes", mock_gauge)

    # When/Then (should not raise)
    worker_metrics.clear_worker_metrics()

    # Then
    assert mock_gauge.remove_called_with == str(mock_pid)


def test_clear_worker_metrics__valueerror__silently_handles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    mock_pid = 67890
    mock_gauge = MockGauge()
    mock_gauge.should_raise_on_remove = ValueError("Invalid label")

    monkeypatch.setattr(worker_metrics.os, "getpid", lambda: mock_pid)
    monkeypatch.setattr(worker_metrics, "flagsmith_worker_rss_bytes", mock_gauge)

    # When/Then (should not raise)
    worker_metrics.clear_worker_metrics()

    # Then
    assert mock_gauge.remove_called_with == str(mock_pid)