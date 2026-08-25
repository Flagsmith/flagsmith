export type UsageTone = 'success' | 'warning' | 'danger'

export type PlanLimit = number | null | undefined

export const usagePercent = (usage: number, limit: PlanLimit): number =>
  limit && limit > 0 ? Math.round((usage / limit) * 100) : 0

export const boundPercent = (percent: number): number =>
  Math.min(Math.max(percent, 0), 100)

export const toneFor = (percent: number, warnAt: number): UsageTone => {
  if (percent >= 100) return 'danger'
  if (percent >= warnAt) return 'warning'
  return 'success'
}
