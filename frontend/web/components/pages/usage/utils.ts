import {
  BillingPeriod,
  PeriodOption,
  periodOptions,
  rollingPeriodOptions,
} from 'common/types/requests'
import { Subscription } from 'common/types/responses'
import { PlanLimit } from 'components/shared/UsageBar/utils'

export type PeriodSelection = BillingPeriod | 'default'

export type RollingReason = 'free' | 'invoiced' | 'unavailable'

export type UsageBasis =
  | { window: 'billing-period' }
  | { window: 'rolling'; reason: RollingReason }

const rollingReason = (
  subscription: Subscription | undefined,
  isFreePlan: boolean,
): RollingReason => {
  if (isFreePlan) {
    return 'free'
  }
  // Only Chargebee sends the billing terms, so the others never have one.
  return subscription?.payment_method === 'CHARGEBEE'
    ? 'unavailable'
    : 'invoiced'
}

export const usageBasisOf = (
  subscription: Subscription | undefined,
  isFreePlan: boolean,
): UsageBasis =>
  !isFreePlan && subscription?.has_active_billing_periods
    ? { window: 'billing-period' }
    : { reason: rollingReason(subscription, isFreePlan), window: 'rolling' }

export const isBilledOnAPeriod = (basis: UsageBasis): boolean =>
  basis.window === 'billing-period'

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

  return {
    hint: `Where your organisation stands against its allowance, over ${allowanceWindowLabel(
      basis,
    )}.`,
    title: 'Your plan',
  }
}

export const basisExplanation = (basis: UsageBasis): string | undefined => {
  if (basis.window === 'billing-period') {
    return undefined
  }

  switch (basis.reason) {
    case 'invoiced':
      return 'Billing periods come from Chargebee, and this organisation is invoiced outside it.'
    case 'unavailable':
      return 'No billing period has reached us from Chargebee for this organisation yet.'
    default:
      return undefined
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
