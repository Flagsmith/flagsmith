import {
  BillingPeriod,
  PeriodOption,
  periodOptions,
  rollingPeriodOptions,
} from 'common/types/requests'
import { Subscription } from 'common/types/responses'
import { PlanLimit } from 'components/shared/UsageBar/utils'

export type PeriodSelection = BillingPeriod | 'default'

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

// charge_for_api_call_count_overages only bills Start-Up and Scale-Up.
// Enterprise falls through its match and is never charged. Mirrors
// SubscriptionPlanFamily.get_by_plan_id.
export const isChargedForOverages = (
  subscription: Subscription | undefined,
): boolean => {
  const plan = (subscription?.plan ?? '').replace(/-/g, '').toLowerCase()
  return plan.startsWith('startup') || plan.startsWith('scaleup')
}

export const planSectionCopy = (
  basis: UsageBasis,
  limit: PlanLimit,
): { title: string; hint: string } => {
  if (!limit) {
    return {
      hint: `API calls over ${allowanceWindowLabel(
        basis,
      )}. This installation has no plan limit.`,
      title: 'Your usage',
    }
  }

  if (basis.window === 'rolling' && basis.reason === 'no-period') {
    return {
      hint: `Usage against your plan limit over ${allowanceWindowLabel(
        basis,
      )}. We are unable to show exact billing periods for your subscription plan.`,
      title: 'Your plan',
    }
  }

  return {
    hint: `Usage against your plan limit over ${allowanceWindowLabel(basis)}.`,
    title: 'Your plan',
  }
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

export const contributionNote = (
  projectName: string,
  scopedTotal: number,
  organisationTotal: number,
): string | undefined => {
  if (organisationTotal <= 0) {
    return undefined
  }

  const percent = Math.round((scopedTotal / organisationTotal) * 100)

  return `${projectName} accounts for ${percent}% of that usage.`
}

// The note sits under the meter, so it can only compare over the window the
// meter shows. On any other period "that usage" would name a figure that is
// not on screen.
export const showsContribution = (
  basis: UsageBasis,
  period: BillingPeriod,
  projectId: number | undefined,
): boolean => !!projectId && period === allowanceWindow(basis)

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
