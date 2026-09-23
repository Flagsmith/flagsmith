import moment from 'moment'
import { CurrentBillingPeriod } from 'common/types/responses'

export type BillingPeriodCopy = {
  range: string
  resets: string
  daysLeft: number
}

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
  // The end is exclusive, so the last instant inside it can fall on the same
  // day when a term does not start at midnight.
  const lastDay = ends.clone().subtract(1, 'millisecond')
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
