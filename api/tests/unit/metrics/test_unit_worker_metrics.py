from pathlib import Path

import pytest

from metrics import worker_metrics


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
