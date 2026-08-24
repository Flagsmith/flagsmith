import {
  BillingPeriod,
  PeriodOption,
  periodOptions,
  rollingPeriodOptions,
} from 'common/types/requests'
import { Subscription } from 'common/types/responses'

/** Distinguishes "not chosen yet" from the rolling window, which is undefined. */
export type PeriodSelection = BillingPeriod | 'default'

/**
 * A billing term is what makes usage accumulate towards a reset. Plans without
 * one, free and most enterprise agreements, run on rolling windows instead.
 *
 * The plan lookup stays with the caller: resolving it pulls in the Flux stores,
 * which cannot load outside a browser.
 */
export const planHasBillingPeriod = (
  subscription: Subscription | undefined,
  isFreePlan: boolean,
): boolean => !isFreePlan && !!subscription?.has_active_billing_periods

/**
 * The default depends on the plan, which only arrives after the first render,
 * so an explicit choice is stored and 'default' resolves once the plan is known.
 */
export const resolvePeriod = (
  chosen: PeriodSelection,
  billingPeriodAvailable: boolean,
): BillingPeriod => {
  if (chosen !== 'default') {
    return chosen
  }
  return billingPeriodAvailable ? 'current_billing_period' : undefined
}

/**
 * Whether the period being *viewed* accumulates towards the limit. A billed
 * organisation can still choose a rolling window, and 90 days of usage must
 * not be drawn against a monthly allowance.
 */
export const isBillingPeriodSelected = (period: BillingPeriod): boolean =>
  period === 'current_billing_period' || period === 'previous_billing_period'

/** Without a billing term the billing-period options cannot be selected. */
export const periodsFor = (billingPeriodAvailable: boolean): PeriodOption[] =>
  billingPeriodAvailable ? periodOptions : rollingPeriodOptions
