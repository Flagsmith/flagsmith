import { Res } from 'common/types/responses'
import { PlanLimit } from 'components/shared/UsageBar/utils'
import { cumulativeTotals, dailyTotals } from './components/UsageOverTime/utils'

export type OverLimit = {
  limit: number
  overBy: number
  /** Undefined when the rows do not cover the crossing. */
  crossedOn: string | undefined
}

// Same running total the chart draws, so the two cannot disagree.
export const limitCrossedOn = (
  data: Res['organisationUsage'] | undefined,
  limit: PlanLimit,
): string | undefined =>
  limit
    ? cumulativeTotals(dailyTotals(data)).find(
        (point) => point.cumulative >= limit,
      )?.day
    : undefined

export const overLimitOf = (
  total: number,
  limit: PlanLimit,
  data: Res['organisationUsage'] | undefined,
): OverLimit | undefined =>
  limit && total > limit
    ? { crossedOn: limitCrossedOn(data, limit), limit, overBy: total - limit }
    : undefined
