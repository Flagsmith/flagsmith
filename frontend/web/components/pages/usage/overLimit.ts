import { Res } from 'common/types/responses'
import Format from 'common/utils/format'
import { PlanLimit } from 'components/shared/UsageBar/utils'
import { cumulativeTotals, dailyTotals } from './components/UsageOverTime/utils'
import { allowanceWindowLabel, UsageBasis } from './utils'

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

// Whether the charge lands at all is #8264, which needs the API to say so,
// so this still hedges.
const chargeWarning = (basis: UsageBasis, mayBeCharged: boolean): string =>
  mayBeCharged
    ? ` Overage charges may apply over ${allowanceWindowLabel(basis)}.`
    : ''

export const overLimitBannerCopy = (
  over: OverLimit,
  basis: UsageBasis,
  mayBeCharged = false,
): { title: string; body: string } => ({
  body: [
    `You reached 100% of your ${Format.shortenNumber(over.limit)} plan limit`,
    over.crossedOn ? ` on ${over.crossedOn}` : '',
    '.',
    chargeWarning(basis, mayBeCharged),
    ' Your usage stays visible below so you can see what happened.',
  ].join(''),
  title: 'Your organisation has exceeded its plan limit',
})

export const overLimitNote = (over: OverLimit): string =>
  `${Format.shortenNumber(over.overBy)} calls over your ${Format.shortenNumber(
    over.limit,
  )} limit.`
