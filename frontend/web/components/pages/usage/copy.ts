import Format from 'common/utils/format'
import { PlanLimit } from 'components/shared/UsageBar/utils'
import { OverLimit } from './overLimit'
import { BannerKind, BannerState } from './bannerState'
import { allowanceWindowLabel, UsageBasis } from './utils'

/**
 * Everything the usage page says about a plan and its limit, in one place, so
 * a sentence cannot drift into two versions of itself.
 */

const sentences = (...parts: (string | false | undefined)[]): string =>
  parts.filter(Boolean).join(' ')

const calls = (count: number): string => (count === 1 ? 'call' : 'calls')

// Only the overage is evidence the limit was reached. block_access_to_admin
// says an organisation is blocked, not why, and support can set it by hand.
// Names no window: the same sentence serves a limit measured over a billing
// period and one measured over the last 30 days.
const limitReached = (over: OverLimit | undefined): string | undefined =>
  over &&
  `You reached your plan limit of ${Format.shortenNumber(
    over.limit,
  )} API ${calls(over.limit)}${over.crossedOn ? ` on ${over.crossedOn}` : ''}.`

/** Every sentence that does not depend on a number. */
const COPY = {
  // Neither route works for a block support set by hand: the plan-change hook
  // and the unrestricting task both skip organisations with no
  // APILimitAccessBlock, so this is all we can offer without evidence.
  askSupport: 'Contact support to restore access.',
  flagsPaused: 'Flags are not being served for your organisation.',
  noBillingPeriod:
    'We are unable to show exact billing periods for your subscription plan.',
  noPlanLimit: 'This installation has no plan limit.',
  overLimitTitle: 'Your organisation has exceeded its plan limit',
  planTitle: 'Your plan',
  recovery:
    'Upgrading restores access straight away. Otherwise access returns once' +
    ' your usage has stayed under the limit for 30 days.',
  restrictedTitle: 'Your organisation is restricted',
  staysVisible: 'Your usage stays visible below so you can see what happened.',
  usageTitle: 'Your usage',
}

export type BannerCopy = { title: string; body: string }

type OverLimitKind = Exclude<BannerKind, 'restricted'>

/** What each over-limit banner adds between the overage and the footer. */
const OVER_LIMIT_MESSAGE: Record<
  OverLimitKind,
  (over: OverLimit, window: string) => string | undefined
> = {
  'over-limit': () => undefined,
  // The charge is settled at the end of the period, so this states what
  // holds now and what would change it.
  'overage-charged': (_, window) => `Overage charges will apply for ${window}.`,
  'overage-covered': (over, window) =>
    `Your first overage is covered for ${window}, unless usage reaches ${Format.shortenNumber(
      2 * over.limit,
    )} API calls. Overages after this will be charged.`,
  'restriction-after-grace': () =>
    'If usage stays over the limit, your organisation will be restricted after 7 days.',
  // The restriction task runs every 12 hours.
  'restriction-imminent': () =>
    'Your 7 day grace period has already been used, so your organisation can be restricted within 12 hours.',
}

export const bannerCopy = (
  state: BannerState,
  basis: UsageBasis,
): BannerCopy => {
  if (state.kind === 'restricted') {
    return {
      body: sentences(
        state.flagsPaused && COPY.flagsPaused,
        state.over
          ? sentences(limitReached(state.over), COPY.recovery)
          : COPY.askSupport,
      ),
      title: COPY.restrictedTitle,
    }
  }

  return {
    body: sentences(
      limitReached(state.over),
      OVER_LIMIT_MESSAGE[state.kind](state.over, allowanceWindowLabel(basis)),
      COPY.staysVisible,
    ),
    title: COPY.overLimitTitle,
  }
}

export const overLimitNote = (over: OverLimit): string =>
  `${Format.shortenNumber(over.overBy)} ${calls(
    over.overBy,
  )} over your ${Format.shortenNumber(over.limit)} limit.`

export const planSectionCopy = (
  basis: UsageBasis,
  limit: PlanLimit,
): { title: string; hint: string } => {
  const window = allowanceWindowLabel(basis)

  if (!limit) {
    return {
      hint: sentences(`API calls over ${window}.`, COPY.noPlanLimit),
      title: COPY.usageTitle,
    }
  }

  return {
    hint: sentences(
      `Usage against your plan limit over ${window}.`,
      basis.window === 'rolling' &&
        basis.reason === 'no-period' &&
        COPY.noBillingPeriod,
    ),
    title: COPY.planTitle,
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
