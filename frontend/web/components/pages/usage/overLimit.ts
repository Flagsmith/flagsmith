import { Res } from 'common/types/responses'
import Format from 'common/utils/format'
import { PlanLimit } from 'components/shared/UsageBar/utils'
import { cumulativeTotals, dailyTotals } from './components/UsageOverTime/utils'
import { allowanceWindowLabel, isBilledOnAPeriod, UsageBasis } from './utils'

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

// Overages are only billed against a Chargebee term, so a rolling window
// cannot be charged for one. Charged or covered by grace is #8264.
const chargeWarning = (basis: UsageBasis): string =>
  isBilledOnAPeriod(basis)
    ? ` Overage charges may apply over ${allowanceWindowLabel(basis)}.`
    : ''

export const overLimitBannerCopy = (
  over: OverLimit,
  basis: UsageBasis,
): { title: string; body: string } => ({
  body: [
    `You reached 100% of your ${Format.shortenNumber(over.limit)} plan limit`,
    over.crossedOn ? ` on ${over.crossedOn}` : '',
    '.',
    chargeWarning(basis),
    ' Your usage stays visible below so you can see what happened.',
  ].join(''),
  title: 'Your organisation has exceeded its plan limit',
})

export const overLimitNote = (over: OverLimit): string =>
  `${Format.shortenNumber(over.overBy)} calls over your ${Format.shortenNumber(
    over.limit,
  )} limit.`
