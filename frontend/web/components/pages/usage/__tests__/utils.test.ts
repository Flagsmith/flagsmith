import { Subscription } from 'common/types/responses'
import {
  isBillingPeriodSelected,
  planHasBillingPeriod,
  periodsFor,
  resolvePeriod,
} from 'components/pages/usage/utils'

const subscription = (values: Partial<Subscription>): Subscription =>
  ({ has_active_billing_periods: false, plan: null, ...values } as Subscription)

describe('UsageDashboard utils', () => {
  describe('planHasBillingPeriod', () => {
    it('is true for a paid plan with active billing periods', () => {
      expect(
        planHasBillingPeriod(
          subscription({ has_active_billing_periods: true }),
          false,
        ),
      ).toBe(true)
    })

    // Enterprise agreements are not billed through Chargebee, so they carry a
    // limit but no term.
    it('is false for a paid plan without active billing periods', () => {
      expect(
        planHasBillingPeriod(
          subscription({ has_active_billing_periods: false }),
          false,
        ),
      ).toBe(false)
    })

    it('is false on the free plan even if the flag is somehow set', () => {
      expect(
        planHasBillingPeriod(
          subscription({ has_active_billing_periods: true }),
          true,
        ),
      ).toBe(false)
    })

    it('is false before the subscription has loaded', () => {
      expect(planHasBillingPeriod(undefined, false)).toBe(false)
    })
  })

  // A billed organisation can still pick a rolling window, and 90 days of
  // usage must not be drawn against a monthly allowance.
  describe('isBillingPeriodSelected', () => {
    it.each`
      period                       | expected
      ${'current_billing_period'}  | ${true}
      ${'previous_billing_period'} | ${true}
      ${'90_day_period'}           | ${false}
      ${undefined}                 | ${false}
    `('$period is a billing period: $expected', ({ expected, period }) => {
      expect(isBillingPeriodSelected(period)).toBe(expected)
    })
  })

  describe('resolvePeriod', () => {
    it('defaults to the current billing period when there is one', () => {
      expect(resolvePeriod('default', true)).toBe('current_billing_period')
    })

    it('defaults to the rolling window when there is not', () => {
      expect(resolvePeriod('default', false)).toBeUndefined()
    })

    it('keeps an explicit choice', () => {
      expect(resolvePeriod('90_day_period', true)).toBe('90_day_period')
      expect(resolvePeriod('previous_billing_period', true)).toBe(
        'previous_billing_period',
      )
    })

    // 'Last 30 days' is undefined, so it has to survive rather than fall back.
    it('keeps an explicit rolling-window choice on a billed plan', () => {
      expect(resolvePeriod(undefined, true)).toBeUndefined()
    })
  })

  describe('periodsFor', () => {
    it('offers the billing periods only when there is a term', () => {
      expect(periodsFor(true).map((period) => period.value)).toContain(
        'current_billing_period',
      )
      expect(periodsFor(false).map((period) => period.value)).not.toContain(
        'current_billing_period',
      )
    })

    it('always offers the rolling windows', () => {
      for (const periods of [periodsFor(true), periodsFor(false)]) {
        expect(periods.map((period) => period.value)).toEqual(
          expect.arrayContaining(['90_day_period', undefined]),
        )
      }
    })
  })
})
