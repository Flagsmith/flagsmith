import rehearse
from setup_experiment import RateLimited


def test_measured_results__refresh_is_rate_limited__waits_for_warehouse_counts(
    monkeypatch,
):
    # Given a cooldown followed by an asynchronous warehouse refresh
    expected = {"guided": {"exposed": 2, "converted": 1}}
    result = {
        "payload": {
            "metrics": [{"metric_id": 1, "variants": {"guided": {"n": 2, "sum": 1}}}]
        }
    }
    now = 100
    refreshes = []

    def request(path, data=None):
        if path.endswith("refresh/"):
            refreshes.append(now)
            if len(refreshes) == 1:
                raise RateLimited("6")
            return None
        return {"results": result if now >= 109 else None}

    def sleep(seconds):
        nonlocal now
        now += seconds

    monkeypatch.setattr(rehearse, "request", request)
    monkeypatch.setattr(rehearse.time, "monotonic", lambda: now)
    monkeypatch.setattr(rehearse.time, "sleep", sleep)

    # When the rehearsal requests the measured results
    measured = rehearse.measured_results("experiment/", 1, expected)

    # Then it retries at the server's deadline and returns the worker's result
    assert measured == result
    assert refreshes == [100, 106]
