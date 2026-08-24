import { Res, UsageEventsList } from 'common/types/responses'

/** The four fields an event is billed on. */
const COUNTED = [
  'flags',
  'identities',
  'traits',
  'environment_document',
] as const

const sum = (
  events: UsageEventsList[],
  key: (typeof COUNTED)[number],
): number => events.reduce((running, event) => running + (event[key] ?? 0), 0)

export const usageEvent = (
  values: Partial<UsageEventsList> = {},
): UsageEventsList => ({
  day: '2026-08-01',
  environment_document: 0,
  flags: 0,
  identities: 0,
  labels: { user_agent: null },
  traits: 0,
  ...values,
})

/**
 * Totals are derived rather than supplied, so a fixture cannot claim a total
 * that its own events disagree with, and no cast is needed to omit them.
 */
export const usageResponse = (
  events: UsageEventsList[],
): Res['organisationUsage'] => ({
  events_list: events,
  totals: {
    environmentDocument: sum(events, 'environment_document'),
    flags: sum(events, 'flags'),
    identities: sum(events, 'identities'),
    total: COUNTED.reduce((running, key) => running + sum(events, key), 0),
    traits: sum(events, 'traits'),
  },
})
