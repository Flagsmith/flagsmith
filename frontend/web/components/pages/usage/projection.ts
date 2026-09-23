import moment from 'moment'
import { CurrentBillingPeriod } from 'common/types/responses'
import { PlanLimit } from 'components/shared/UsageBar/utils'

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

  const periodMs = ends.diff(starts)
  const elapsedMs = now.diff(starts)
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
