import { Subscription } from 'common/types/responses'
import {
  contributionNote,
  isBillingPeriodSelected,
  allowanceWindow,
  planSectionCopy,
  basisExplanation,
  allowanceWindowLabel,
  showsPlanCeiling,
  usageBasisOf,
  periodsFor,
  resolvePeriod,
} from 'components/pages/usage/utils'

const subscription = (values: Partial<Subscription>): Subscription =>
  ({ has_active_billing_periods: false, plan: null, ...values } as Subscription)

describe('UsageDashboard utils', () => {
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

  describe('contributionNote', () => {
    it('says what share of the organisation a project accounts for', () => {
      expect(contributionNote('Checkout', 400000, 1000000)).toBe(
        'Checkout accounts for 40% of that usage.',
      )
    })

    it('has nothing to say when the organisation used nothing', () => {
      expect(contributionNote('Checkout', 0, 0)).toBeUndefined()
    })

    it('never reports a project as more than all of the usage', () => {
      expect(contributionNote('Checkout', 1000000, 1000000)).toBe(
        'Checkout accounts for 100% of that usage.',
      )
    })
  })

  describe('planSectionCopy', () => {
    const rolling = { reason: 'free', window: 'rolling' } as const

    it('measures against the allowance when there is one', () => {
      const copy = planSectionCopy(rolling, 50000)

      expect(copy.title).toBe('Your plan')
      expect(copy.hint).toContain('against its allowance')
    })

    it('claims no allowance where there is none to claim', () => {
      const copy = planSectionCopy(rolling, null)

      expect(copy.title).toBe('Your usage')
      expect(copy.hint).toContain('no plan limit')
      expect(copy.hint).not.toContain('allowance')
    })
  })

  describe('usageBasisOf', () => {
    it('measures a billed organisation over its billing period', () => {
      const basis = usageBasisOf(
        subscription({ has_active_billing_periods: true }),
        false,
      )

      expect(basis).toEqual({ window: 'billing-period' })
      expect(allowanceWindow(basis)).toBe('current_billing_period')
      expect(allowanceWindowLabel(basis)).toBe('this billing period')
      expect(basisExplanation(basis)).toBeUndefined()
    })

    it('measures a free plan over the trailing 30 days, by design', () => {
      const basis = usageBasisOf(subscription({}), true)

      expect(basis).toEqual({ reason: 'free', window: 'rolling' })
      expect(allowanceWindow(basis)).toBeUndefined()
      expect(basisExplanation(basis)).toBeUndefined()
    })

    it('says an invoiced organisation will never have a billing period', () => {
      const basis = usageBasisOf(
        subscription({ payment_method: 'XERO' }),
        false,
      )

      expect(basis).toEqual({ reason: 'invoiced', window: 'rolling' })
      expect(basisExplanation(basis)).toContain('invoiced outside it')
    })

    it('separates a Chargebee organisation whose period has not arrived', () => {
      const basis = usageBasisOf(
        subscription({ payment_method: 'CHARGEBEE' }),
        false,
      )

      expect(basis).toEqual({ reason: 'unavailable', window: 'rolling' })
      expect(basisExplanation(basis)).toContain('has reached us')
    })
  })

  describe('showsPlanCeiling', () => {
    it('draws the ceiling for the organisation over a comparable period', () => {
      expect(showsPlanCeiling(undefined, undefined)).toBe(true)
      expect(showsPlanCeiling('current_billing_period', undefined)).toBe(true)
    })

    it('drops it for one project, which will never reach the ceiling', () => {
      expect(showsPlanCeiling(undefined, 12)).toBe(false)
    })

    it('drops it for the 90 day window', () => {
      expect(showsPlanCeiling('90_day_period', undefined)).toBe(false)
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
