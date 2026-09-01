import {
  limitCrossedOn,
  OverLimit,
  overLimitBannerCopy,
  overLimitNote,
  overLimitOf,
} from 'components/pages/usage/overLimit'
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

describe('overLimit', () => {
  describe('overLimitOf', () => {
    it('is nothing until usage passes the limit', () => {
      expect(overLimitOf(50000, 50000, days([50000]))).toBeUndefined()
      expect(overLimitOf(49999, 50000, days([49999]))).toBeUndefined()
    })

    it('is nothing when the plan has no limit to pass', () => {
      expect(overLimitOf(9999999, null, days([9999999]))).toBeUndefined()
    })

    it('reports how far over, and carries the limit it is over', () => {
      const over = overLimitOf(60000, 50000, days([60000]))

      expect(over?.overBy).toBe(10000)
      expect(over?.limit).toBe(50000)
    })
  })

  describe('limitCrossedOn', () => {
    it('names the day the running total reached the limit', () => {
      expect(limitCrossedOn(days([40, 40, 40, 40]), 100)).toBe('3 Aug')
    })

    // The API returns a row per day per user agent, so a day only counts once
    // its rows are added together.
    it('adds up the rows a day is split across', () => {
      const data = usageResponse([
        usageEvent({ day: '2026-08-01', flags: 60 }),
        usageEvent({ day: '2026-08-01', identities: 60 }),
        usageEvent({ day: '2026-08-02', flags: 10 }),
      ])

      expect(limitCrossedOn(data, 100)).toBe('1 Aug')
    })

    it('reads the days in order, whatever order they arrive in', () => {
      const data = usageResponse([
        usageEvent({ day: '2026-08-03', flags: 40 }),
        usageEvent({ day: '2026-08-01', flags: 40 }),
        usageEvent({ day: '2026-08-02', flags: 40 }),
      ])

      expect(limitCrossedOn(data, 100)).toBe('3 Aug')
    })

    it('says nothing when the days never reach the limit', () => {
      expect(limitCrossedOn(days([10, 10]), 100)).toBeUndefined()
      expect(limitCrossedOn(undefined, 100)).toBeUndefined()
    })
  })

  describe('copy', () => {
    it('names the day when the data shows it', () => {
      const over = exceeding(60000, 50000, days([40000, 20000]))

      expect(overLimitBannerCopy(over, billed).body).toContain(
        'plan limit on 2 Aug',
      )
    })

    // Defensive: the totals and the daily rows come from one response, so a
    // total over the limit normally has a crossing day somewhere in the rows.
    it('leaves the day out when the rows are missing', () => {
      const over = exceeding(60000, 50000)

      expect(overLimitBannerCopy(over, billed).body).toContain(
        'plan limit. Overage',
      )
    })

    it('measures the overage over the window the meter shows', () => {
      const over = exceeding(60000, 50000, days([60000]))

      expect(overLimitBannerCopy(over, billed).body).toContain(
        'this billing period',
      )
      expect(
        overLimitBannerCopy(over, { window: 'rolling' } as UsageBasis).body,
      ).toContain('the last 30 days')
    })

    it('says how far over in the note under the meter', () => {
      const over = exceeding(60000, 50000, days([60000]))

      expect(overLimitNote(over)).toBe('10K calls over your 50K limit.')
    })
  })
})
