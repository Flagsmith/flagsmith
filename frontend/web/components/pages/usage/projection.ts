import moment from 'moment'
import { CurrentBillingPeriod } from 'common/types/responses'
import Format from 'common/utils/format'
import { PlanLimit } from 'components/shared/UsageBar/utils'
import { lastDayOf } from './billingPeriod'

/**
 * How much of the period must have passed before an average means anything.
 * A fifth is about six days of a monthly period.
 */
export const MIN_ELAPSED_SHARE = 0.2

export type Projection = {
  /** Calls the period is on track to reach, at the rate so far. */
  total: number
  percentOfLimit: number | undefined
  overLimit: boolean
}

/** A straight line through usage so far, not a forecast. */
export const projectUsage = (
  total: number,
  limit: PlanLimit,
  period: CurrentBillingPeriod | null | undefined,
): Projection | undefined => {
  if (!period) {
    return undefined
  }

  const starts = moment.utc(period.starts_at)
  const ends = moment.utc(period.ends_at)
  const now = moment.utc()
  if (!starts.isValid() || !ends.isValid()) {
    return undefined
  }

  // Once the period is over the figure is the total, not an estimate, and
  // the billing strip already says it ended.
  if (!now.isBefore(ends)) {
    return undefined
  }

  // Elapsed comes from the clock, not from the last day with usage on it.
  // The response carries no row for a quiet day, so the last row is the last
  // day with traffic, and dividing by that would inflate a rate that stopped.
  const periodMs = ends.diff(starts)
  const elapsedMs = Math.min(now.diff(starts), periodMs)
  if (periodMs <= 0 || elapsedMs <= 0) {
    return undefined
  }

  const elapsedShare = Math.min(elapsedMs / periodMs, 1)
  if (elapsedShare < MIN_ELAPSED_SHARE) {
    return undefined
  }

  const projected = Math.round(total / elapsedShare)

  return {
    overLimit: !!limit && projected > limit,
    percentOfLimit: limit ? Math.round((projected / limit) * 100) : undefined,
    total: projected,
  }
}

export const projectionNote = (
  projection: Projection,
  periodEndsAt: string,
): string => {
  const landing = `Estimated to reach ~${Format.shortenNumber(
    projection.total,
  )}`
  const share =
    projection.percentOfLimit === undefined
      ? ''
      : ` (${projection.percentOfLimit}% of your limit)`
  // The last day inside the period, so the sentence names the day the chart's
  // line stops on rather than the reset a day later.
  const by = ` by ${lastDayOf(periodEndsAt).format('D MMM')}.`

  return projection.overLimit
    ? `${landing}${share}${by} That lands over your limit.`
    : `${landing}${share}${by}`
}
