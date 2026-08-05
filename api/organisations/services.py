from datetime import datetime

from dateutil.relativedelta import relativedelta


def get_current_billing_period_start_date(
    billing_term_starts_at: datetime,
    now: datetime,
) -> datetime:
    """
    Return the start of the monthly period an organisation is currently in.

    A billing term can be longer than a month, an annual plan being the common
    case, but API usage is allowed per month. The current period therefore
    starts at the most recent monthly anniversary of the term start, which for
    a term that began more than a year ago means counting the years as well as
    the months.
    """
    elapsed = relativedelta(now, billing_term_starts_at)
    months_elapsed = elapsed.years * 12 + elapsed.months
    return billing_term_starts_at + relativedelta(months=months_elapsed)
