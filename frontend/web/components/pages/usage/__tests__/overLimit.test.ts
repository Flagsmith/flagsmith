import { limitCrossedOn, overLimitOf } from 'components/pages/usage/overLimit'
import { usageEvent, usageResponse } from './fixtures'

const days = (perDay: number[]) =>
  usageResponse(
    perDay.map((flags, index) =>
      usageEvent({ day: `2026-08-${`${index + 1}`.padStart(2, '0')}`, flags }),
    ),
  )

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
})
