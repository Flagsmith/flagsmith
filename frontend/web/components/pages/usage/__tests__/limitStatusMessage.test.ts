import { limitStatusMessage } from 'components/pages/usage/limitStatusMessage'
import { LimitStatus } from 'components/pages/usage/limitStatus'
import { OverLimit, overLimitOf } from 'components/pages/usage/overLimit'
import { UsageBasis } from 'components/pages/usage/utils'
import { usageEvent, usageResponse } from './fixtures'

const billed: UsageBasis = { window: 'billing-period' }
const rolling = { window: 'rolling' } as UsageBasis

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

const over = exceeding(60000, 50000, days([40000, 20000]))

describe('limitStatusMessage', () => {
  it('names the day when the data shows it', () => {
    expect(limitStatusMessage({ kind: 'over-limit', over }, billed).body).toBe(
      'You reached your plan limit of 50K API calls on 2 Aug.' +
        ' Your usage stays visible below so you can see what happened.',
    )
  })

  // Artificial: totals and rows always arrive in the same response.
  it('leaves the day out when the rows are missing', () => {
    const { body } = limitStatusMessage(
      { kind: 'over-limit', over: exceeding(60000, 50000) },
      billed,
    )

    expect(body).toContain('your plan limit of 50K API calls.')
    expect(body).not.toContain(' on ')
  })

  it.each`
    kind                         | expected
    ${'overage-covered'}         | ${'Your first overage is covered for this billing period, unless usage reaches 100K API calls. Overages after this will be charged.'}
    ${'overage-charged'}         | ${'Overage charges will apply for this billing period.'}
    ${'restriction-after-grace'} | ${'If usage stays over the limit, your organisation will be restricted 7 days after it first went over.'}
    ${'restriction-imminent'}    | ${'Your 7 day grace period has already been used, so your organisation can be restricted within 12 hours.'}
  `('explains what happens next for $kind', ({ expected, kind }) => {
    const { body, title } = limitStatusMessage(
      { kind, over } as LimitStatus,
      billed,
    )

    expect(title).toBe('Your organisation has exceeded its plan limit')
    expect(body).toBe(
      'You reached your plan limit of 50K API calls on 2 Aug.' +
        ` ${expected}` +
        ' Your usage stays visible below so you can see what happened.',
    )
  })

  it('names the rolling window where there is no billing period', () => {
    expect(
      limitStatusMessage({ kind: 'overage-charged', over }, rolling).body,
    ).toContain('Overage charges will apply for the last 30 days.')
  })

  it('tells a restricted organisation how to get access back', () => {
    const { body, title } = limitStatusMessage(
      { flagsPaused: false, kind: 'restricted', over },
      billed,
    )

    expect(title).toBe('Your organisation is restricted')
    expect(body).toBe(
      'You reached your plan limit of 50K API calls on 2 Aug.' +
        ' Upgrading restores access straight away. Otherwise access returns' +
        ' once your usage has stayed under the limit for 30 days.',
    )
  })

  it('says flags are paused when serving has stopped', () => {
    expect(
      limitStatusMessage(
        { flagsPaused: true, kind: 'restricted', over },
        billed,
      ).body,
    ).toMatch(/^Flags are not being served for your organisation\. /)
  })

  // Most of that 30 day window has no overage left to report.
  it('explains the restriction with no overage to report', () => {
    const { body } = limitStatusMessage(
      { flagsPaused: false, kind: 'restricted', over: undefined },
      billed,
    )

    // block_access_to_admin can be set by hand, and neither recovery route
    // works for such a block, so with no overage in evidence we promise
    // nothing.
    expect(body).toBe('Contact support to restore access.')
  })
})
