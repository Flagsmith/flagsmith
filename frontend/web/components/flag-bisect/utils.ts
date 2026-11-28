import {
  FlagBisectIncident,
  FlagBisectState,
  FlagBisectSuspect,
} from 'common/types/responses'

export const LIVE_STATES: FlagBisectState[] = [
  'INVESTIGATING',
  'AWAITING_APPROVAL',
  'PROBING',
  'CONFIRMING',
  'IDENTIFIED',
  'REMEDIATION_PROPOSED',
  'REMEDIATED',
]

export type Tone = 'danger' | 'warning' | 'success' | 'info'

export const stateTone = (state: FlagBisectState): Tone => {
  switch (state) {
    case 'RESOLVED':
    case 'REMEDIATED':
      return 'success'
    case 'AWAITING_APPROVAL':
    case 'IDENTIFIED':
    case 'REMEDIATION_PROPOSED':
    case 'CONFIRMING':
      return 'warning'
    case 'NOT_A_FLAG_CHANGE':
    case 'INCONCLUSIVE':
      return 'info'
    default:
      return 'danger'
  }
}

export const stateLabel = (state: FlagBisectState): string =>
  state.charAt(0) + state.slice(1).toLowerCase().replace(/_/g, ' ')

export const percent = (value: number, digits = 1): string =>
  `${(value * 100).toFixed(digits)}%`

export const describeValue = (
  enabled: boolean,
  value: string | number | boolean | null,
): string => {
  if (!enabled) return 'off'
  if (value === null || value === '') return 'on'
  return `on (${String(value)})`
}

export const describeChange = (suspect: FlagBisectSuspect): string =>
  `${describeValue(
    suspect.before_enabled,
    suspect.before_value,
  )} → ${describeValue(suspect.after_enabled, suspect.after_value)}`

export const culpritNames = (incident: FlagBisectIncident): string[] => {
  const ids = new Set(incident.conclusion?.ids ?? [])
  return incident.suspects
    .filter((s) => ids.has(String(s.feature)))
    .map((s) => s.feature_name)
}

/** The human step the incident is waiting on, if any. */
export const pendingGate = (
  state: FlagBisectState,
): 'envelope' | 'propose' | 'approve' | null => {
  if (state === 'AWAITING_APPROVAL') return 'envelope'
  if (state === 'IDENTIFIED') return 'propose'
  if (state === 'REMEDIATION_PROPOSED') return 'approve'
  return null
}

export const headline = (incident: FlagBisectIncident): string => {
  const culprits = culpritNames(incident)
  if (culprits.length) return `Culprit: ${culprits.join(' + ')}`
  if (incident.state === 'NOT_A_FLAG_CHANGE') {
    return 'None of these flag changes caused it'
  }
  return `Failure rate ${percent(incident.baseline_rate)} → ${percent(
    incident.regression_rate,
  )}`
}

/** The `detail` an API error carries, without asserting the error's type. */
export const errorDetail = (error: unknown): string => {
  if (typeof error === 'object' && error !== null && 'data' in error) {
    const data: unknown = error.data
    if (
      typeof data === 'object' &&
      data !== null &&
      'detail' in data &&
      typeof data.detail === 'string'
    ) {
      return data.detail
    }
  }
  return 'The request failed.'
}
