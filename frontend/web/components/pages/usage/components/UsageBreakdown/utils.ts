import {
  colorChart1,
  colorChart2,
  colorChart3,
  colorChart4,
} from 'common/theme/tokens'
import { Res, UsageEventsList } from 'common/types/responses'

export type BreakdownDimension = 'request-type' | 'sdk'

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
  { label: 'By SDK', value: 'sdk' },
]

export type RequestTypeKey =
  | 'flags'
  | 'identities'
  | 'environment_document'
  | 'traits'

export const REQUEST_TYPES: {
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
