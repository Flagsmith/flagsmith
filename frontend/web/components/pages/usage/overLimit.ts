import { Res } from 'common/types/responses'
import Format from 'common/utils/format'
import { PlanLimit } from 'components/shared/UsageBar/utils'
import { cumulativeTotals, dailyTotals } from './components/UsageOverTime/utils'
import { allowanceWindowLabel, UsageBasis } from './utils'

export type OverLimit = {
  limit: number
  /** Calls served beyond the plan limit. */
  overBy: number
  /** The day the running total passed the limit, if it is in the data. */
  crossedOn: string | undefined
}

// Read off the same running total the chart draws, so the day named here and
// the point the line crosses the ceiling cannot disagree.
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

export const overLimitBannerCopy = (
  over: OverLimit,
  basis: UsageBasis,
): { title: string; body: string } => ({
  // Whether the overage is charged or covered by the grace period is #8264,
  // which needs the API to say so. Until then this has to hedge.
  body: [
    `You reached 100% of your ${Format.shortenNumber(over.limit)} plan limit`,
    over.crossedOn ? ` on ${over.crossedOn}` : '',
    `. Overage charges may apply over ${allowanceWindowLabel(basis)}.`,
    ' Your usage stays visible below so you can see what happened.',
  ].join(''),
  title: 'Your organisation has exceeded its plan limit',
})

export const overLimitNote = (over: OverLimit): string =>
  `${Format.shortenNumber(over.overBy)} calls over your ${Format.shortenNumber(
    over.limit,
  )} limit.`
