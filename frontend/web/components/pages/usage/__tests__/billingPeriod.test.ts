import { billingPeriodCopy } from 'components/pages/usage/billingPeriod'

const period = (starts_at: string, ends_at: string) => ({ ends_at, starts_at })

describe('billingPeriodCopy', () => {
  beforeEach(() => {
    jest.useFakeTimers().setSystemTime(new Date('2026-07-21T00:00:00Z'))
  })
  afterEach(() => {
    jest.useRealTimers()
  })

  it('describes a period within one year', () => {
    const copy = billingPeriodCopy(
      period('2026-07-01T00:00:00Z', '2026-08-01T00:00:00Z'),
    )

    // The end is exclusive, so the range stops on the last day inside it.
    expect(copy?.range).toBe('1 Jul – 31 Jul 2026')
    expect(copy?.resets).toBe('Resets in 11 days · 1 Aug 2026')
    expect(copy?.daysLeft).toBe(11)
  })

  it('repeats the year when the period crosses one', () => {
    const copy = billingPeriodCopy(
      period('2026-12-15T00:00:00Z', '2027-01-15T00:00:00Z'),
    )

    expect(copy?.range).toBe('15 Dec 2026 – 14 Jan 2027')
  })

  it('says today on the last day rather than in 0 days', () => {
    const copy = billingPeriodCopy(
      period('2026-06-21T00:00:00Z', '2026-07-21T06:00:00Z'),
    )

    expect(copy?.resets).toBe('Resets today · 21 Jul 2026')
    expect(copy?.daysLeft).toBe(0)
  })

  it('singularises the last full day', () => {
    const copy = billingPeriodCopy(
      period('2026-06-22T00:00:00Z', '2026-07-22T00:00:00Z'),
    )

    expect(copy?.resets).toBe('Resets in 1 day · 22 Jul 2026')
  })

  // Free plans and a stale cache both arrive as null.
  it.each([null, undefined])('has nothing to say for %p', (value) => {
    expect(billingPeriodCopy(value)).toBeUndefined()
  })

  it('never counts backwards once the period has passed', () => {
    const copy = billingPeriodCopy(
      period('2026-05-01T00:00:00Z', '2026-06-01T00:00:00Z'),
    )

    expect(copy?.daysLeft).toBe(0)
  })
})
