import { Res } from 'common/types/responses'
import { PlanLimit } from 'components/shared/UsageBar/utils'
import Format from 'common/utils/format'
import { cumulativeTotals, dailyTotals } from './components/UsageOverTime/utils'
import { calls } from './sentences'

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

export const overLimitNote = (over: OverLimit): string =>
  `${Format.shortenNumber(over.overBy)} ${calls(
    over.overBy,
  )} over your ${Format.shortenNumber(over.limit)} limit.`
