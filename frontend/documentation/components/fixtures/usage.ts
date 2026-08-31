import { Res, UsageEventsList } from 'common/types/responses'
import approachingTheLimit from './usage/approaching-the-limit.json'
import currentBillingPeriod from './usage/current-billing-period.json'
import freePlan from './usage/free-plan.json'
import last30Days from './usage/last-30-days.json'
import last90Days from './usage/last-90-days.json'
import overTheLimit from './usage/over-the-limit.json'
import previousBillingPeriod from './usage/previous-billing-period.json'

type DailyCounts = {
  day: string
  flags: number
  identities: number
  traits: number
  environment_document: number
}

const sum = (
  events: UsageEventsList[],
  key: 'flags' | 'identities' | 'traits' | 'environment_document',
): number => events.reduce((running, event) => running + (event[key] ?? 0), 0)

// The API returns one row per day and client type, so the fixtures split each
// day the same way, otherwise the SDK breakdown has nothing to group on.
const SDK_SPLIT: [string | null, number][] = [
  ['flagsmith-python/3.9.1', 0.42],
  ['flagsmith-java/7.2.0', 0.31],
  ['flagsmith-nodejs/5.0.4', 0.19],
  [null, 0.08],
]

export const toUsageResponse = (
  days: DailyCounts[],
  share = 1,
): Res['organisationUsage'] => {
  const events: UsageEventsList[] = days.flatMap((day) =>
    SDK_SPLIT.map(([userAgent, weight]) => ({
      day: day.day,
      environment_document: Math.round(
        day.environment_document * share * weight,
      ),
      flags: Math.round(day.flags * share * weight),
      identities: Math.round(day.identities * share * weight),
      labels: { user_agent: userAgent },
      traits: Math.round(day.traits * share * weight),
    })),
  )

  return {
    events_list: events,
    totals: {
      environmentDocument: sum(events, 'environment_document'),
      flags: sum(events, 'flags'),
      identities: sum(events, 'identities'),
      total:
        sum(events, 'flags') +
        sum(events, 'identities') +
        sum(events, 'traits') +
        sum(events, 'environment_document'),
      traits: sum(events, 'traits'),
    },
  }
}

export const USAGE_SCENARIOS = {
  approachingTheLimit,
  currentBillingPeriod,
  freePlan,
  last30Days,
  last90Days,
  overTheLimit,
  previousBillingPeriod,
} as const
