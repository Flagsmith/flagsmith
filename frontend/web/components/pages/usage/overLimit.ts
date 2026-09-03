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

// unrestrict_after_api_limit_grace_period_is_stale lifts the block once no
// 100% notification has fired for 30 days, and a plan change clears it at
// once. What is actually paused needs stop_serving_flags on the response
// (#8256), so this says access rather than naming a service.
// Takes no OverLimit: the block outlives going over it, so through that
// 30 day window usage is back under the limit and there is nothing to report.
export const restrictedBannerCopy = (
  over: OverLimit | undefined,
): { title: string; body: string } => ({
  body: [
    over
      ? `You went over your ${Format.shortenNumber(over.limit)} plan limit${
          over.crossedOn ? ` on ${over.crossedOn}` : ''
        }. `
      : '',
    'Upgrading restores access straight away. Otherwise it returns 30 days',
    ' after your usage drops back under the limit.',
  ].join(''),
  title: 'Your organisation is restricted',
})

export type BannerContext = {
  /** The organisation is on a plan that gets billed for overages. */
  mayBeCharged?: boolean
  /** Admin access has already been cut off. */
  isRestricted?: boolean
}

export const overLimitBannerCopy = (
  over: OverLimit,
  basis: UsageBasis,
  { isRestricted, mayBeCharged }: BannerContext = {},
): { title: string; body: string } =>
  isRestricted
    ? restrictedBannerCopy(over)
    : {
        body: [
          `You reached 100% of your ${Format.shortenNumber(
            over.limit,
          )} plan limit`,
          over.crossedOn ? ` on ${over.crossedOn}` : '',
          '.',
          chargeWarning(basis, !!mayBeCharged),
          ' Your usage stays visible below so you can see what happened.',
        ].join(''),
        title: 'Your organisation has exceeded its plan limit',
      }

export const overLimitNote = (over: OverLimit): string =>
  `${Format.shortenNumber(over.overBy)} calls over your ${Format.shortenNumber(
    over.limit,
  )} limit.`
