import Format from 'common/utils/format'
import { PlanLimit } from 'components/shared/UsageBar/utils'
import { OverLimit } from './overLimit'
import { allowanceWindowLabel, UsageBasis } from './utils'

/**
 * Everything the usage page says about a plan and its limit, in one place, so
 * a sentence cannot drift into two versions of itself.
 */

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

export const planSectionCopy = (
  basis: UsageBasis,
  limit: PlanLimit,
): { title: string; hint: string } => {
  const window = allowanceWindowLabel(basis)

  if (!limit) {
    return {
      hint: `API calls over ${window}. This installation has no plan limit.`,
      title: 'Your usage',
    }
  }

  return {
    hint: sentences(
      `Usage against your plan limit over ${window}.`,
      basis.window === 'rolling' &&
        basis.reason === 'no-period' &&
        'We are unable to show exact billing periods for your subscription plan.',
    ),
    title: 'Your plan',
  }
}

export const contributionNote = (
  projectName: string,
  scopedTotal: number,
  organisationTotal: number,
): string | undefined =>
  organisationTotal > 0
    ? `${projectName} accounts for ${Math.round(
        (scopedTotal / organisationTotal) * 100,
      )}% of that usage.`
    : undefined
