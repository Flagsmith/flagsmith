from types import SimpleNamespace

import pytest

from metrics import worker_metrics


def test_get_current_process_max_rss_bytes__resource_usage_available__returns_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    max_rss_kib = 123
    fake_resource = SimpleNamespace(
        RUSAGE_SELF=1,
        getrusage=lambda who: SimpleNamespace(ru_maxrss=max_rss_kib),
    )
    monkeypatch.setattr(worker_metrics, "resource", fake_resource)

    # When
    result = worker_metrics.get_current_process_max_rss_bytes()

    # Then
    assert result == max_rss_kib * worker_metrics.MAX_RSS_KIB_TO_BYTES


def test_get_current_process_max_rss_bytes__resource_usage_available__uses_current_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    requested_resource = None
    rusage_self = 1

    def fake_getrusage(who: int) -> SimpleNamespace:
        nonlocal requested_resource
        requested_resource = who
        return SimpleNamespace(ru_maxrss=123)

    fake_resource = SimpleNamespace(
        RUSAGE_SELF=rusage_self,
        getrusage=fake_getrusage,
    )
    monkeypatch.setattr(worker_metrics, "resource", fake_resource)

    # When
    worker_metrics.get_current_process_max_rss_bytes()

    # Then
    assert requested_resource == rusage_self


def test_get_current_process_max_rss_bytes__resource_module_unavailable__returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.setattr(worker_metrics, "resource", None)

    # When
    result = worker_metrics.get_current_process_max_rss_bytes()

    # Then
    assert result is None


def test_get_current_process_max_rss_bytes__max_rss_missing__returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    fake_resource = SimpleNamespace(
        RUSAGE_SELF=1,
        getrusage=lambda who: SimpleNamespace(),
    )
    monkeypatch.setattr(worker_metrics, "resource", fake_resource)

    # When
    result = worker_metrics.get_current_process_max_rss_bytes()

    # Then
    assert result is None


def test_get_current_process_max_rss_bytes__max_rss_invalid__returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    fake_resource = SimpleNamespace(
        RUSAGE_SELF=1,
        getrusage=lambda who: SimpleNamespace(ru_maxrss=-1),
    )
    monkeypatch.setattr(worker_metrics, "resource", fake_resource)

    # When
    result = worker_metrics.get_current_process_max_rss_bytes()

    # Then
    assert result is None


def test_get_current_process_max_rss_bytes__resource_error__returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    def fake_getrusage(who: int) -> SimpleNamespace:
        raise OSError("resource usage unavailable")

    fake_resource = SimpleNamespace(
        RUSAGE_SELF=1,
        getrusage=fake_getrusage,
    )
    monkeypatch.setattr(worker_metrics, "resource", fake_resource)

    # When
    result = worker_metrics.get_current_process_max_rss_bytes()

    # Then
    assert result is None
