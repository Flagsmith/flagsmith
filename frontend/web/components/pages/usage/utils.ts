import {
  BillingPeriod,
  PeriodOption,
  periodOptions,
  rollingPeriodOptions,
} from 'common/types/requests'
import { Organisation, Subscription } from 'common/types/responses'
import { PlanLimit } from 'components/shared/UsageBar/utils'

export type PeriodSelection = BillingPeriod | 'default'

// 'free' reads like any other rolling window on purpose. The seven days
// before flags stop only applies to a first breach: OrganisationBreachedGracePeriod
// is written on the first restriction and never deleted, and
// restrict_use_due_to_api_limit_grace_period_over drops the wait once it exists.
// The API does not say which case an organisation is in.
export type RollingReason = 'free' | 'no-period'

export type UsageBasis =
  | { window: 'billing-period' }
  | { window: 'rolling'; reason: RollingReason }

export const usageBasisOf = (
  subscription: Subscription | undefined,
  isFreePlan: boolean,
): UsageBasis =>
  !isFreePlan && subscription?.has_active_billing_periods
    ? { window: 'billing-period' }
    : // A free plan has no billing period by design and needs no explaining. A
      // paid one is worth saying out loud, whether it is invoiced directly, was
      // set up by hand, or the dates have gone stale.
      { reason: isFreePlan ? 'free' : 'no-period', window: 'rolling' }

export const isBilledOnAPeriod = (basis: UsageBasis): boolean =>
  basis.window === 'billing-period'

export type OverageStatus =
  | 'not_charged'
  | 'within_limit'
  | 'covered'
  | 'charged'

// Mirrors charge_for_api_call_count_overages: the first overage is forgiven
// once, unless usage reaches twice the limit.
export const overageStatusOf = (
  organisation:
    | Pick<
        Organisation,
        'overage_billing_eligible' | 'api_limit_grace_period_used'
      >
    | undefined,
  total: number,
  limit: PlanLimit,
): OverageStatus => {
  if (!organisation?.overage_billing_eligible || !limit) return 'not_charged'
  if (total <= limit) return 'within_limit'
  if (organisation.api_limit_grace_period_used || total >= 2 * limit) {
    return 'charged'
  }
  return 'covered'
}

// The restriction task skips the 7 day wait once a grace row exists.
export type RestrictionWarning = 'after-grace' | 'next-check'

export const restrictionWarningOf = (
  organisation:
    | Pick<
        Organisation,
        'api_limit_restriction_enabled' | 'api_limit_grace_period_used'
      >
    | undefined,
): RestrictionWarning | undefined => {
  if (!organisation?.api_limit_restriction_enabled) return undefined
  return organisation.api_limit_grace_period_used ? 'next-check' : 'after-grace'
}

export const resolvePeriod = (
  chosen: PeriodSelection,
  billingPeriodAvailable: boolean,
): BillingPeriod => {
  if (chosen !== 'default') {
    return chosen
  }
  return billingPeriodAvailable ? 'current_billing_period' : undefined
}

export const isBillingPeriodSelected = (period: BillingPeriod): boolean =>
  period === 'current_billing_period' || period === 'previous_billing_period'

// The note sits under the meter, so it can only compare over the window the
// meter shows. On any other period "that usage" would name a figure that is
// not on screen.
export const showsContribution = (
  basis: UsageBasis,
  period: BillingPeriod,
  projectId: number | undefined,
): boolean => !!projectId && period === allowanceWindow(basis)

// The chart projects towards one period end, so it can only draw a projection
// for the period that end belongs to, over the whole organisation.
export const showsProjection = (
  period: BillingPeriod,
  projectId: number | undefined,
): boolean => period === 'current_billing_period' && !projectId

export const showsPlanCeiling = (
  period: BillingPeriod,
  projectId: number | undefined,
): boolean => period !== '90_day_period' && !projectId

export const allowanceWindow = (basis: UsageBasis): BillingPeriod =>
  isBilledOnAPeriod(basis) ? 'current_billing_period' : undefined

export const allowanceWindowLabel = (basis: UsageBasis): string =>
  isBilledOnAPeriod(basis) ? 'this billing period' : 'the last 30 days'

export const periodLabel = (
  periods: PeriodOption[],
  period: BillingPeriod,
): string => periods.find((option) => option.value === period)?.label ?? ''

export const periodsFor = (billingPeriodAvailable: boolean): PeriodOption[] =>
  billingPeriodAvailable ? periodOptions : rollingPeriodOptions
