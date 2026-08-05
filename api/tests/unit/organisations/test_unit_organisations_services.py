from datetime import UTC, datetime

import pytest

from organisations.services import get_current_billing_period_start_date


@pytest.mark.parametrize(
    "billing_term_starts_at, now, expected",
    [
        pytest.param(
            datetime(2026, 1, 10, 9, 0, tzinfo=UTC),
            datetime(2026, 1, 20, 9, 0, tzinfo=UTC),
            datetime(2026, 1, 10, 9, 0, tzinfo=UTC),
            id="first_month_of_the_term",
        ),
        pytest.param(
            datetime(2026, 1, 10, 9, 0, tzinfo=UTC),
            datetime(2026, 5, 3, 9, 0, tzinfo=UTC),
            datetime(2026, 4, 10, 9, 0, tzinfo=UTC),
            id="part_way_through_a_monthly_term",
        ),
        pytest.param(
            # An annual term, well over a year old: the months-only delta used
            # to drop the years and land a period a year early.
            datetime(2024, 9, 15, 9, 0, tzinfo=UTC),
            datetime(2026, 7, 2, 9, 0, tzinfo=UTC),
            datetime(2026, 6, 15, 9, 0, tzinfo=UTC),
            id="term_older_than_a_year",
        ),
        pytest.param(
            datetime(2024, 9, 15, 9, 0, tzinfo=UTC),
            datetime(2026, 9, 15, 9, 0, tzinfo=UTC),
            datetime(2026, 9, 15, 9, 0, tzinfo=UTC),
            id="exactly_on_an_anniversary",
        ),
    ],
)
def test_get_current_billing_period_start_date__returns_latest_monthly_anniversary(
    billing_term_starts_at: datetime,
    now: datetime,
    expected: datetime,
) -> None:
    # When
    result = get_current_billing_period_start_date(billing_term_starts_at, now)

    # Then
    assert result == expected
    assert result <= now
