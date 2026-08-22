import { Res, UsageEventsList } from 'common/types/responses'

export type BreakdownDimension =
  | 'request-type'
  | 'project'
  | 'environment'
  | 'sdk'

export type BreakdownRow = {
  /** Unique within a breakdown. Names can repeat, so rows key on this. */
  key: string
  label: string
  value: number
}

export const BREAKDOWN_DIMENSIONS: {
  label: string
  value: BreakdownDimension
}[] = [
  { label: 'By request type', value: 'request-type' },
  { label: 'By project', value: 'project' },
  { label: 'By environment', value: 'environment' },
  { label: 'By SDK', value: 'sdk' },
]

/** The countable fields on an event, as opposed to its day and its labels. */
export type RequestTypeKey =
  | 'flags'
  | 'identities'
  | 'environment_document'
  | 'traits'

/**
 * The four types an API call is billed as, named as the usage page has always
 * named them so the rows line up with the "what counts" definitions.
 */
export const REQUEST_TYPES: { key: RequestTypeKey; label: string }[] = [
  { key: 'flags', label: 'Flags' },
  { key: 'identities', label: 'Identities' },
  { key: 'environment_document', label: 'Environment Document' },
  { key: 'traits', label: 'Traits' },
]

const countOf = (event: UsageEventsList, key: RequestTypeKey): number =>
  event[key] ?? 0

/** Every request in an event, whatever it was billed as. */
export const totalOf = (event: UsageEventsList): number =>
  REQUEST_TYPES.reduce((sum, { key }) => sum + countOf(event, key), 0)

/** Rows sort by size, because the question is always "what is the biggest". */
const ranked = (rows: BreakdownRow[]): BreakdownRow[] =>
  rows.filter((row) => row.value > 0).sort((a, b) => b.value - a.value)

export const byRequestType = (
  data: Res['organisationUsage'] | undefined,
): BreakdownRow[] => {
  const events = data?.events_list ?? []

  return ranked(
    REQUEST_TYPES.map(({ key, label }) => ({
      key,
      label,
      value: events.reduce((sum, event) => sum + countOf(event, key), 0),
    })),
  )
}

/**
 * Older events predate user-agent capture, so they carry no SDK. They are
 * grouped rather than dropped, otherwise the rows would not sum to the total.
 */
export const bySdk = (
  data: Res['organisationUsage'] | undefined,
): BreakdownRow[] => {
  const totals = new Map<string, number>()

  for (const event of data?.events_list ?? []) {
    const label = event.labels?.user_agent || 'Unknown'
    totals.set(label, (totals.get(label) ?? 0) + totalOf(event))
  }

  return ranked(
    [...totals.entries()].map(([label, value]) => ({
      key: label,
      label,
      value,
    })),
  )
}

/** One request per scope, so each total arrives already attributed to a row. */
export const fromScopedTotals = (
  scopes: { key: string; label: string }[],
  totals: Record<string, number | undefined>,
): BreakdownRow[] =>
  ranked(
    scopes.map(({ key, label }) => ({
      key,
      label,
      value: totals[key] ?? 0,
    })),
  )
