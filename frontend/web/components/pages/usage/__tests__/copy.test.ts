import {
  overLimitBannerCopy,
  overLimitNote,
  restrictedBannerCopy,
} from 'components/pages/usage/copy'
import { OverLimit, overLimitOf } from 'components/pages/usage/overLimit'
import { UsageBasis } from 'components/pages/usage/utils'
import { usageEvent, usageResponse } from './fixtures'

const billed: UsageBasis = { window: 'billing-period' }

const days = (perDay: number[]) =>
  usageResponse(
    perDay.map((flags, index) =>
      usageEvent({ day: `2026-08-${`${index + 1}`.padStart(2, '0')}`, flags }),
    ),
  )

// overLimitOf is undefined below the limit; every copy test is above it.
const exceeding = (
  total: number,
  limit: number,
  data?: ReturnType<typeof days>,
) => overLimitOf(total, limit, data) as OverLimit

describe('usage copy', () => {
  it('names the day when the data shows it', () => {
    const over = exceeding(60000, 50000, days([40000, 20000]))

    expect(overLimitBannerCopy(over, billed).body).toContain(
      'plan limit on 2 Aug',
    )
  })

  // Artificial: totals and rows always arrive in the same response.
  it('leaves the day out when the rows are missing', () => {
    const over = exceeding(60000, 50000)

    const { body } = overLimitBannerCopy(over, billed)

    expect(body).toContain('your 50K plan limit.')
    expect(body).not.toContain(' on ')
  })

  it('warns about charges only where they can be charged', () => {
    const over = exceeding(60000, 50000, days([60000]))

    expect(
      overLimitBannerCopy(over, billed, { mayBeCharged: true }).body,
    ).toContain('Overage charges may apply over this billing period.')
    expect(overLimitBannerCopy(over, billed).body).not.toContain(
      'Overage charges',
    )
    expect(
      overLimitBannerCopy(over, { window: 'rolling' } as UsageBasis, {
        mayBeCharged: true,
      }).body,
    ).not.toContain('this billing period')
  })

  it('still reports the overage itself on a rolling window', () => {
    const over = exceeding(60000, 50000, days([40000, 20000]))
    const body = overLimitBannerCopy(over, {
      window: 'rolling',
    } as UsageBasis).body

    expect(body).toContain('You reached your 50K plan limit on 2 Aug.')
    expect(body).toContain('Your usage stays visible below')
  })

  it('tells a restricted organisation how to get access back', () => {
    const over = exceeding(60000, 50000, days([40000, 20000]))
    const { body, title } = restrictedBannerCopy(over)

    expect(title).toBe('Your organisation is restricted')
    expect(body).toContain('You reached your 50K plan limit on 2 Aug.')
    expect(body).toContain('stayed under the limit for 30 days')
    // The charge is not the point once they are already cut off.
    expect(body).not.toContain('Overage charges')
  })

  // Most of that 30 day window has no overage left to report.
  it('explains the restriction with no overage to report', () => {
    const { body, title } = restrictedBannerCopy(undefined)

    expect(title).toBe('Your organisation is restricted')
    expect(body).toContain('stayed under the limit for 30 days')
    // block_access_to_admin can be set by hand, so with no overage in
    // evidence the copy must not claim the limit was reached.
    expect(body).not.toContain('plan limit')
  })

  it('says how far over in the note under the meter', () => {
    const over = exceeding(60000, 50000, days([60000]))

    expect(overLimitNote(over)).toBe('10K calls over your 50K limit.')
    // shortenNumber leaves small counts alone, so one is reachable.
    expect(overLimitNote(exceeding(50001, 50000, days([50001])))).toBe(
      '1 call over your 50K limit.',
    )
  })
})
