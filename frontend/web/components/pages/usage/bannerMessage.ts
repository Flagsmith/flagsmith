import Format from 'common/utils/format'
import { OverLimit } from './overLimit'
import { BannerKind, BannerState } from './bannerState'
import { calls, sentences } from './sentences'
import { allowanceWindowLabel, UsageBasis } from './utils'

export type BannerMessage = { title: string; body: string }

// Only the overage is evidence the limit was reached. block_access_to_admin
// says an organisation is blocked, not why, and support can set it by hand.
// Names no window: the same sentence serves a limit measured over a billing
// period and one measured over the last 30 days.
const limitReached = (over: OverLimit): string =>
  `You reached your plan limit of ${Format.shortenNumber(
    over.limit,
  )} API ${calls(over.limit)}${over.crossedOn ? ` on ${over.crossedOn}` : ''}.`

const OVER_LIMIT_TITLE = 'Your organisation has exceeded its plan limit'
const RESTRICTED_TITLE = 'Your organisation is restricted'
const STAYS_VISIBLE =
  'Your usage stays visible below so you can see what happened.'
const FLAGS_PAUSED = 'Flags are not being served for your organisation.'
const RECOVERY =
  'Upgrading restores access straight away. Otherwise access returns once' +
  ' your usage has stayed under the limit for 30 days.'
// Neither route works for a block support set by hand: the plan-change hook
// and the unrestricting task both skip organisations with no
// APILimitAccessBlock, so this is all we can offer without evidence.
const ASK_SUPPORT = 'Contact support to restore access.'

type OverLimitKind = Exclude<BannerKind, 'restricted'>

/** What each over-limit banner adds between the overage and the footer. */
const OVER_LIMIT_MESSAGE: Record<
  OverLimitKind,
  (over: OverLimit, window: string) => string | undefined
> = {
  'over-limit': () => undefined,
  'overage-charged': (_, window) => `Overage charges will apply for ${window}.`,
  // The charge is settled at the end of the period, so this states what
  // holds now and what would change it.
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

export const bannerMessage = (
  state: BannerState,
  basis: UsageBasis,
): BannerMessage => {
  if (state.kind === 'restricted') {
    return {
      body: sentences(
        state.flagsPaused && FLAGS_PAUSED,
        state.over
          ? sentences(limitReached(state.over), RECOVERY)
          : ASK_SUPPORT,
      ),
      title: RESTRICTED_TITLE,
    }
  }

  return {
    body: sentences(
      limitReached(state.over),
      OVER_LIMIT_MESSAGE[state.kind](state.over, allowanceWindowLabel(basis)),
      STAYS_VISIBLE,
    ),
    title: OVER_LIMIT_TITLE,
  }
}
