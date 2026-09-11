import moment from 'moment'
import { CurrentBillingPeriod } from 'common/types/responses'

export type BillingPeriodCopy = {
  range: string
  resets: string
  daysLeft: number
}

/**
 * The strip's two halves. Undefined outside a billing term, where there is no
 * period to describe.
 */
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

  // The year is only worth repeating when the period crosses into a new one.
  const startFormat = starts.isSame(ends, 'year') ? 'D MMM' : 'D MMM YYYY'
  // Inclusive: a period ending on the 1st runs through the last day of the
  // month before it.
  const lastDay = ends.clone().subtract(1, 'day')
  const daysLeft = Math.max(ends.diff(moment.utc(), 'days'), 0)

  return {
    daysLeft,
    range: `${starts.format(startFormat)} – ${lastDay.format('D MMM YYYY')}`,
    resets: `Resets ${
      daysLeft === 0
        ? 'today'
        : `in ${daysLeft} ${daysLeft === 1 ? 'day' : 'days'}`
    } · ${ends.format('D MMM YYYY')}`,
  }
}
