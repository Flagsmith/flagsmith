import { Subscription } from 'common/types/responses'
import {
  isBillingPeriodSelected,
  isChargedForOverages,
  allowanceWindow,
  allowanceWindowLabel,
  showsContribution,
  showsPlanCeiling,
  usageBasisOf,
  periodsFor,
  resolvePeriod,
} from 'components/pages/usage/utils'
import { contributionNote, planSectionCopy } from 'components/pages/usage/copy'

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
      expect(copy.hint).toContain('against your plan limit')
    })

    it('claims no allowance where there is none to claim', () => {
      const copy = planSectionCopy(rolling, null)

      expect(copy.title).toBe('Your usage')
      expect(copy.hint).toContain('no plan limit')
      expect(copy.hint).not.toContain('allowance')
    })
  })

  describe('isChargedForOverages', () => {
    it.each`
      plan             | expected
      ${'start-up'}    | ${true}
      ${'startup-v2'}  | ${true}
      ${'scale-up-v2'} | ${true}
      ${'enterprise'}  | ${false}
      ${'free'}        | ${false}
      ${null}          | ${false}
    `('$plan is charged for overages: $expected', ({ expected, plan }) => {
      expect(isChargedForOverages(subscription({ plan }))).toBe(expected)
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
    })

    // Deliberate: see RollingReason.
    it('promises a free plan no deadline it cannot keep', () => {
      const hint = planSectionCopy(
        usageBasisOf(subscription({}), true),
        50000,
      ).hint

      expect(hint).not.toContain('7 day')
      expect(hint).not.toContain('seven day')
      expect(hint).not.toContain('pause')
    })

    it('measures a free plan over the trailing 30 days, by design', () => {
      const basis = usageBasisOf(subscription({}), true)

      expect(basis).toEqual({ reason: 'free', window: 'rolling' })
      expect(allowanceWindow(basis)).toBeUndefined()
      expect(planSectionCopy(basis, 50000).hint).toBe(
        'Usage against your plan limit over the last 30 days.',
      )
    })

    it('says so when a paid organisation has no billing period', () => {
      const basis = usageBasisOf(
        subscription({ payment_method: 'XERO' }),
        false,
      )

      expect(basis).toEqual({ reason: 'no-period', window: 'rolling' })
      expect(planSectionCopy(basis, 50000).hint).toContain(
        'unable to show exact billing periods',
      )
    })
  })

  describe('showsContribution', () => {
    const billed = { window: 'billing-period' } as const
    const rolling = { reason: 'free', window: 'rolling' } as const

    it('compares only over the window the meter is showing', () => {
      expect(showsContribution(billed, 'current_billing_period', 12)).toBe(true)
      expect(showsContribution(rolling, undefined, 12)).toBe(true)
    })

    it('says nothing on a period the meter does not cover', () => {
      expect(showsContribution(billed, '90_day_period', 12)).toBe(false)
      expect(showsContribution(rolling, '90_day_period', 12)).toBe(false)
    })

    it('says nothing without a project', () => {
      expect(
        showsContribution(billed, 'current_billing_period', undefined),
      ).toBe(false)
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
