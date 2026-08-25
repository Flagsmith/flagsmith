import {
  BillingPeriod,
  PeriodOption,
  periodOptions,
  rollingPeriodOptions,
} from 'common/types/requests'
import { Subscription } from 'common/types/responses'

export type PeriodSelection = BillingPeriod | 'default'

export const planHasBillingPeriod = (
  subscription: Subscription | undefined,
  isFreePlan: boolean,
): boolean => !isFreePlan && !!subscription?.has_active_billing_periods

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

export const periodLabel = (
  periods: PeriodOption[],
  period: BillingPeriod,
): string => periods.find((option) => option.value === period)?.label ?? ''

export const periodsFor = (billingPeriodAvailable: boolean): PeriodOption[] =>
  billingPeriodAvailable ? periodOptions : rollingPeriodOptions
