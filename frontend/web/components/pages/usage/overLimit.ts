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

const sentences = (...parts: (string | false | undefined)[]): string =>
  parts.filter(Boolean).join(' ')

// Only the overage is evidence the limit was reached. block_access_to_admin
// says an organisation is blocked, not why, and support can set it by hand.
const limitReached = (over: OverLimit | undefined): string | undefined =>
  over &&
  `You reached your ${Format.shortenNumber(over.limit)} plan limit${
    over.crossedOn ? ` on ${over.crossedOn}` : ''
  }.`

// Says access, not flags: the API does not expose stop_serving_flags.
const RECOVERY =
  'Upgrading restores access straight away. Otherwise access returns once' +
  ' your usage has stayed under the limit for 30 days.'

const STAYS_VISIBLE =
  'Your usage stays visible below so you can see what happened.'

export type BannerContext = {
  /** The organisation is on a plan that gets billed for overages. */
  mayBeCharged?: boolean
}

// The block outlives going over the limit, so the overage is optional here.
export const restrictedBannerCopy = (
  over: OverLimit | undefined,
): { title: string; body: string } => ({
  body: sentences(limitReached(over), RECOVERY),
  title: 'Your organisation is restricted',
})

export const overLimitBannerCopy = (
  over: OverLimit,
  basis: UsageBasis,
  { mayBeCharged }: BannerContext = {},
): { title: string; body: string } => ({
  body: sentences(
    limitReached(over),
    // Hedged: the API does not say whether the charge actually lands.
    mayBeCharged &&
      `Overage charges may apply over ${allowanceWindowLabel(basis)}.`,
    STAYS_VISIBLE,
  ),
  title: 'Your organisation has exceeded its plan limit',
})

export const overLimitNote = (over: OverLimit): string =>
  `${Format.shortenNumber(over.overBy)} ${
    over.overBy === 1 ? 'call' : 'calls'
  } over your ${Format.shortenNumber(over.limit)} limit.`
