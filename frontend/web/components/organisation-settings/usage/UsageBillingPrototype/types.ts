/**
 * PROTOTYPE (#8184). The view model the usage page renders.
 *
 * It is deliberately shaped like the response we want the API to return, so
 * that swapping fixtures for real endpoints is a change of source rather than
 * a rewrite of the page. See `usePrototypeUsage`.
 */

export type PlanKind = 'free' | 'paid'

/**
 * Grace period, as designed in "Grace period states". Paid orgs get one
 * billing month up to 200%; free orgs get 7 days after crossing 100%.
 */
export type GraceState =
  | 'available' // under the limit, grace intact
  | 'covering' // paid, first month at 100-200%, not charged
  | 'used' // paid, later month over 100% or any month at 200%+, charged
  | 'countdown' // free, over 100%, inside the 7-day window
  | 'restricted' // free, window elapsed, access stopped

export type UsagePeriod = {
  label: string
  /** Human date, e.g. "9 Aug 2026". Comes from the billing term today. */
  resetsAt: string
  daysRemaining: number
  /** False for the rolling windows (last 30 / 90 days). */
  isBillingPeriod: boolean
}

export type UsagePoint = {
  day: string
  cumulative: number
}

export type BreakdownRow = {
  label: string
  /** Canonical operation name, shared with the "what counts" docs. */
  op: string
  value: number
}

export type UsageNotification = {
  percent: number
  enabled: boolean
}

export type UsageView = {
  plan: PlanKind
  period: UsagePeriod
  total: number
  limit: number | null
  series: UsagePoint[]
  breakdown: BreakdownRow[]
  grace: GraceState
  /** Only set while `grace` is 'countdown'. */
  graceDaysLeft?: number
  /** Free orgs past the grace window: flag serving and admin access stopped. */
  restricted: boolean
  /** End-of-period usage at the current run rate. Null when it is too early to say. */
  projected: number | null
  /** Overage in currency. Null until per-org pricing is queryable. */
  overageCost: number | null
  notifications: UsageNotification[]
  channels: { email: boolean; inApp: boolean }
}
