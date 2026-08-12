import { Req } from 'common/types/requests'

/**
 * PROTOTYPE (#8184). The view model the usage page renders.
 *
 * It is deliberately shaped like the response we want the API to return, so
 * that swapping fixtures for real endpoints is a change of source rather than
 * a rewrite of the page. See `usePrototypeUsage`.
 */

export type PlanKind = 'free' | 'paid'

/**
 * Two different things share the name. Paid plans have a grace period: one
 * billing month up to 200%, consumed once and never again. Free plans have a
 * notification period: 7 days after crossing 100%, given every time and never
 * consumed.
 */
export type GraceState =
  | 'available' // under the limit, grace intact
  | 'covering' // paid, first month at 100-200%, not charged
  | 'used' // paid, later month over 100% or any month at 200%+, charged
  | 'countdown' // free, over 100%, inside the 7-day notification period
  | 'restricted' // free, window elapsed, access stopped
  | 'not-applied' // paid, at or above 200%, grace never applies

export type UsagePeriod = {
  label: string
  /** Human date, e.g. "9 Aug 2026". Empty on rolling windows, which never reset. */
  resetsAt: string
  daysRemaining: number
  /** False for the rolling windows (last 30 / 90 days). */
  isBillingPeriod: boolean
  /** Keeps the period selector honest about what is on screen. */
  selectValue: Req['getOrganisationUsage']['billing_period']
}

export type UsagePoint = {
  day: string
  cumulative: number
}

export type BreakdownDimension =
  | 'request-type'
  | 'project'
  | 'environment'
  | 'sdk'

export const BREAKDOWN_DIMENSIONS: {
  value: BreakdownDimension
  label: string
}[] = [
  { label: 'By request type', value: 'request-type' },
  { label: 'By project', value: 'project' },
  { label: 'By environment', value: 'environment' },
  { label: 'By SDK', value: 'sdk' },
]

export type BreakdownRow = {
  label: string
  /** Canonical operation name, shared with the "what counts" docs. */
  op?: string
  value: number
}

export type UsageNotification = {
  percent: number
  enabled: boolean
}

/**
 * What the backend actually notifies on, from
 * `api/organisations/constants.py`. The page showed 75 and 100 only, which is
 * two of eight. Everything above 100 fires once the limit is already passed,
 * so the meter draws only the ones at or below it.
 */
export const USAGE_ALERT_THRESHOLDS = [75, 90, 100, 120, 200, 300, 400, 500]

export type UsageView = {
  plan: PlanKind
  period: UsagePeriod
  total: number
  limit: number | null
  series: UsagePoint[]
  breakdowns: Record<BreakdownDimension, BreakdownRow[]>
  grace: GraceState
  /**
   * Only set while `grace` is 'countdown', and only when the API can say. The
   * lag is 7 days from the qualifying usage notification, but that date is not
   * exposed today, so the UI has to read as "may be paused" without it rather
   * than invent a number.
   */
  graceDaysLeft?: number
  /** Free orgs past the grace window: flag serving and admin access stopped. */
  restricted: boolean
  /** Restricted the same day, because grace had already been used. */
  restrictedImmediately?: boolean
  /** When service comes back on its own, once usage leaves the window. */
  resumesAt?: string
  /** End-of-period usage at the current run rate. Null when it is too early to say. */
  projected: number | null
  /** Days since usage crossed the limit, and the date it happened. */
  daysOverLimit?: number
  overLimitSince?: string
  /** Overage in currency. Null until per-org pricing is queryable. */
  overageCost: number | null
  notifications: UsageNotification[]
  channels: { email: boolean; inApp: boolean }
}
