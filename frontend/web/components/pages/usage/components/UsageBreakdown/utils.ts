import {
  colorChart1,
  colorChart2,
  colorChart3,
  colorChart4,
} from 'common/theme/tokens'
import { UsageGroupBy } from 'common/types/requests'
import { Res, UsageEventsList } from 'common/types/responses'

export type BreakdownDimension =
  | 'request-type'
  | 'project'
  | 'environment'
  | 'sdk'

// Project and environment need their own grouped request; request type and
// SDK come from the rows the page already holds.
export const isGroupedDimension = (
  dimension: BreakdownDimension,
): dimension is UsageGroupBy =>
  dimension === 'project' || dimension === 'environment'

export type BreakdownStatus = 'ready' | 'loading' | 'error' | 'needs-project'

export const groupByOf = (
  dimension: BreakdownDimension,
  projectId: number | undefined,
): UsageGroupBy | undefined => {
  if (!isGroupedDimension(dimension)) return undefined
  // Environments are only ranked within one project.
  if (dimension === 'environment' && !projectId) return undefined
  return dimension
}

export type BreakdownRow = {
  key: string
  label: string
  value: number
  colour?: string
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

type RequestTypeKey = 'flags' | 'identities' | 'environment_document' | 'traits'

const REQUEST_TYPES: {
  key: RequestTypeKey
  label: string
  colour: string
}[] = [
  { colour: colorChart1, key: 'flags', label: 'Flags' },
  { colour: colorChart3, key: 'identities', label: 'Identities' },
  {
    colour: colorChart4,
    key: 'environment_document',
    label: 'Environment Document',
  },
  { colour: colorChart2, key: 'traits', label: 'Traits' },
]

const countOf = (event: UsageEventsList, key: RequestTypeKey): number =>
  event[key] ?? 0

export const totalOf = (event: UsageEventsList): number =>
  REQUEST_TYPES.reduce((sum, { key }) => sum + countOf(event, key), 0)

const ranked = (rows: BreakdownRow[]): BreakdownRow[] =>
  rows.filter((row) => row.value > 0).sort((a, b) => b.value - a.value)

export const byRequestType = (
  data: Res['organisationUsage'] | undefined,
): BreakdownRow[] => {
  const events = data?.events_list ?? []

  return ranked(
    REQUEST_TYPES.map(({ colour, key, label }) => ({
      colour,
      key,
      label,
      value: events.reduce((sum, event) => sum + countOf(event, key), 0),
    })),
  )
}

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

type ScopeKey = 'project_id' | 'environment_id'

// Usage outlives the project or environment that made it, so an id can be
// missing from the names.
export const byScope = (
  data: Res['organisationUsage'] | undefined,
  key: ScopeKey,
  names: Map<number, string>,
  deletedLabel: string,
): BreakdownRow[] => {
  const totals = new Map<number, number>()

  for (const event of data?.events_list ?? []) {
    const id = event[key]
    if (id === null || id === undefined) continue
    totals.set(id, (totals.get(id) ?? 0) + totalOf(event))
  }

  return ranked(
    [...totals.entries()].map(([id, value]) => ({
      key: `${key}-${id}`,
      label: names.get(id) ?? deletedLabel,
      value,
    })),
  )
}

export const sharesOf = (values: number[]): number[] => {
  const total = values.reduce((sum, value) => sum + value, 0)

  if (!total) {
    return values.map(() => 0)
  }

  const exact = values.map((value) => (value / total) * 100)
  const shares = exact.map(Math.floor)
  const byRemainder = exact
    .map((value, index) => ({ index, remainder: value - Math.floor(value) }))
    .sort((a, b) => b.remainder - a.remainder)

  let left = 100 - shares.reduce((sum, share) => sum + share, 0)

  for (const { index } of byRemainder) {
    if (left <= 0) break
    shares[index] += 1
    left -= 1
  }

  return shares
}

export const barPercent = (value: number, largest: number): number => {
  if (value <= 0 || largest <= 0) {
    return 0
  }

  return Math.max(1, Math.round((value / largest) * 100))
}
