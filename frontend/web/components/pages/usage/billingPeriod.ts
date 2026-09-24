import moment from 'moment'
import { CurrentBillingPeriod } from 'common/types/responses'

export type BillingPeriodCopy = {
  range: string
  resets: string
  daysLeft: number
}

/**
 * The last moment inside a period. The API's end is exclusive, so everything
 * that names a day rather than the reset counts from here.
 */
export const lastDayOf = (periodEndsAt: string): moment.Moment =>
  moment.utc(periodEndsAt).subtract(1, 'millisecond')

export const billingPeriodCopy = (
  period: CurrentBillingPeriod | null | undefined,
): BillingPeriodCopy | undefined => {
  if (!period) {
    return undefined
  }

  // Formatted in UTC so the dates read the same as the invoice, rather
  // than shifting a day for anyone whose clock is behind it.
  const starts = moment.utc(period.starts_at)
  const ends = moment.utc(period.ends_at)
  if (!starts.isValid() || !ends.isValid()) {
    return undefined
  }

  const now = moment.utc()
  const startFormat = starts.isSame(ends, 'year') ? 'D MMM' : 'D MMM YYYY'
  const lastDay = lastDayOf(period.ends_at)
  // Calendar days, not whole 24 hour blocks: a reset at midnight tonight is
  // still today, and one at midnight tomorrow is a day away.
  const daysLeft = Math.max(
    ends.clone().startOf('day').diff(now.clone().startOf('day'), 'days'),
    0,
  )

  const reset = ends.format('D MMM YYYY')
  const countdown =
    daysLeft === 0
      ? 'today'
      : `in ${daysLeft} ${daysLeft === 1 ? 'day' : 'days'}`

  return {
    daysLeft,
    range: `${starts.format(startFormat)} – ${lastDay.format('D MMM YYYY')}`,
    resets: ends.isAfter(now)
      ? `Resets ${countdown} · ${reset}`
      : `Ended ${reset}`,
  }
}
