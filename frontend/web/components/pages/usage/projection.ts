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

/**
 * A straight line through usage so far, not a forecast.
 *
 * `lastMeasuredOn` is the last day the usage data covers. Usage arrives a day
 * at a time, so measuring elapsed time against the clock would divide the
 * total by days it does not include yet and read the rate low.
 */
export const projectUsage = (
  total: number,
  limit: PlanLimit,
  period: CurrentBillingPeriod | null | undefined,
  lastMeasuredOn?: string,
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

  const measured = lastMeasuredOn ? moment.utc(lastMeasuredOn) : undefined
  // The total covers whole days, so elapsed runs to the end of the last of
  // them rather than to this instant.
  const measuredThrough =
    measured?.isValid() && measured.isSameOrAfter(starts)
      ? measured.clone().startOf('day').add(1, 'day')
      : now

  const periodMs = ends.diff(starts)
  const elapsedMs = Math.min(measuredThrough.diff(starts), periodMs)
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
