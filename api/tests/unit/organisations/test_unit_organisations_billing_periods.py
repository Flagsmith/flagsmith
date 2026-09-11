from datetime import datetime

import pytest

from organisations.billing_periods import months_elapsed, period_start


@pytest.mark.parametrize(
    "since, now, expected",
    [
        ("2026-09-01T00:00:00+00:00", "2026-09-10T00:00:00+00:00", 0),
        ("2026-01-05T00:00:00+00:00", "2026-09-10T00:00:00+00:00", 8),
        # The year is the part #6099 dropped.
        ("2024-09-03T00:00:00+00:00", "2026-09-10T00:00:00+00:00", 24),
        ("2025-08-07T00:00:00+00:00", "2026-09-11T00:00:00+00:00", 13),
    ],
)
def test_months_elapsed__spans_years__counts_them(
    since: str, now: str, expected: int
) -> None:
    # Given / When
    elapsed = months_elapsed(datetime.fromisoformat(since), datetime.fromisoformat(now))

    # Then
    assert elapsed == expected


@pytest.mark.parametrize(
    "term_starts_at, now, expected",
    [
        # Annual term over a year old. Dropping the year lands in 2025.
        (
            "2024-09-03T00:00:00+00:00",
            "2026-09-10T00:00:00+00:00",
            "2026-09-03T00:00:00+00:00",
        ),
        # February is too short for a 31st, so the window opens on the 28th.
        (
            "2026-01-31T00:00:00+00:00",
            "2026-03-01T00:00:00+00:00",
            "2026-02-28T00:00:00+00:00",
        ),
    ],
)
def test_period_start__long_term__opens_on_the_latest_anniversary(
    term_starts_at: str, now: str, expected: str
) -> None:
    # Given / When
    start = period_start(
        datetime.fromisoformat(term_starts_at), datetime.fromisoformat(now)
    )

    # Then
    assert start == datetime.fromisoformat(expected)
