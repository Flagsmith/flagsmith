export type UsageTone = 'success' | 'warning' | 'danger'

/** Absent for self-hosted, and while the subscription query is in flight. */
export type PlanLimit = number | null | undefined

/** Zero when there is no limit to divide by, so callers get a number either way. */
export const usagePercent = (usage: number, limit: PlanLimit): number =>
  limit && limit > 0 ? Math.round((usage / limit) * 100) : 0

/** The fill width and aria-valuenow both have to stay inside 0-100. */
export const boundPercent = (percent: number): number =>
  Math.min(Math.max(percent, 0), 100)

export const toneFor = (percent: number, warnAt: number): UsageTone => {
  if (percent >= 100) return 'danger'
  if (percent >= warnAt) return 'warning'
  return 'success'
}
