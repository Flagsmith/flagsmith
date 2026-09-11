from datetime import datetime

from dateutil.relativedelta import relativedelta


def months_elapsed(since: datetime, now: datetime) -> int:
    """Whole months between two datetimes, years included."""
    elapsed = relativedelta(now, since)
    return elapsed.years * 12 + elapsed.months


def period_start(billing_term_starts_at: datetime, now: datetime) -> datetime:
    """
    Start of the monthly allowance window a term is currently in. A term can
    run longer than a month, so this is the most recent monthly anniversary of
    its start.
    """
    return billing_term_starts_at + relativedelta(
        months=months_elapsed(billing_term_starts_at, now)
    )
