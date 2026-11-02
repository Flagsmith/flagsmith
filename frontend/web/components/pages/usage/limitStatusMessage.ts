import Format from 'common/utils/format'
import { OverLimit, overLimitNote } from './overLimit'
import { LimitStatusKind, LimitStatus } from './limitStatus'
import { apiCallsWord, joinSentences } from './usageText'
import { allowanceWindowLabel, UsageBasis } from './utils'

export type LimitStatusMessage = { title: string; body: string }

// Names no window, so it serves a billing period and the last 30 days alike.
const limitReached = (over: OverLimit): string =>
  `You reached your plan limit of ${Format.shortenNumber(
    over.limit,
  )} API ${apiCallsWord(over.limit)}${
    over.crossedOn ? ` on ${over.crossedOn}` : ''
  }.`

const OVER_LIMIT_TITLE = 'Your organisation has exceeded its plan limit'
const RESTRICTED_TITLE = 'Your organisation is restricted'
const STAYS_VISIBLE =
  'Your usage stays visible below so you can see what happened.'
const FLAGS_PAUSED = 'Flags are not being served for your organisation.'
// The API does not say whether the block came from API usage or support,
// so this holds for both.
const RECOVERY =
  'If this is due to API usage, access returns after 30 days under the' +
  ' limit or on upgrade. Otherwise, contact support.'

type OverLimitKind = Exclude<LimitStatusKind, 'restricted'>

const OVER_LIMIT_MESSAGE: Record<
  OverLimitKind,
  (over: OverLimit, window: string) => string | undefined
> = {
  'over-limit': () => undefined,
  'overage-charged': (_, window) => `Overage charges will apply for ${window}.`,
  // Settled at the end of the period, so say what would change it.
  'overage-covered': (over, window) =>
    `Your first overage is covered for ${window}, unless usage reaches ${Format.shortenNumber(
      2 * over.limit,
    )} API calls. Overages after this will be charged.`,
  // The task counts the 7 days from the first notification at 100%, not from now.
  'restriction-after-grace': () =>
    'If usage stays over the limit, your organisation will be restricted 7 days after it first went over.',
  // The restriction task runs every 12 hours.
  'restriction-imminent': () =>
    'Your 7 day grace period has already been used, so your organisation can be restricted within 12 hours.',
}

export const limitStatusMessage = (
  status: LimitStatus,
  basis: UsageBasis,
): LimitStatusMessage => {
  if (status.kind === 'restricted') {
    return {
      body: joinSentences(
        status.flagsPaused && FLAGS_PAUSED,
        status.over && limitReached(status.over),
        RECOVERY,
      ),
      title: RESTRICTED_TITLE,
    }
  }

  return {
    body: joinSentences(
      limitReached(status.over),
      OVER_LIMIT_MESSAGE[status.kind](status.over, allowanceWindowLabel(basis)),
      STAYS_VISIBLE,
    ),
    title: OVER_LIMIT_TITLE,
  }
}

const OVERAGE_NOTE: Partial<Record<LimitStatusKind, string>> = {
  'overage-charged': 'Charged at the overage rate.',
  'overage-covered':
    'Covered as your first overage unless usage reaches 2x the limit.',
}

// The line under the meter.
export const limitStatusNote = (
  over: OverLimit,
  kind: LimitStatusKind | undefined,
): string => joinSentences(overLimitNote(over), kind && OVERAGE_NOTE[kind])
