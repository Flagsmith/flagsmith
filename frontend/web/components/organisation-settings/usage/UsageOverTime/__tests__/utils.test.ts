import { Res } from 'common/types/responses'
import {
  cumulativeTotals,
  dailyTotals,
  planLimitThreshold,
  xAxisIntervalFor,
} from 'components/organisation-settings/usage/UsageOverTime/utils'

type UsageEvent = Res['organisationUsage']['events_list'][number]

const event = (day: string, values: Partial<UsageEvent> = {}): UsageEvent =>
  ({
    day,
    environment_document: 0,
    flags: 0,
    identities: 0,
    labels: { user_agent: null },
    traits: 0,
    ...values,
  } as UsageEvent)

const usage = (events: UsageEvent[]) =>
  ({ events_list: events } as Res['organisationUsage'])

describe('UsageOverTime utils', () => {
  describe('dailyTotals', () => {
    it('sums every metric on a day', () => {
      const result = dailyTotals(
        usage([
          event('2026-08-01', {
            environment_document: 1,
            flags: 10,
            identities: 5,
            traits: 2,
          }),
        ]),
      )

      expect(result).toEqual([{ day: '1 Aug', total: 18 }])
    })

    // The API returns a row per day and client type, so a day can appear twice.
    it('collapses several rows for the same day into one point', () => {
      const result = dailyTotals(
        usage([
          event('2026-08-01', { flags: 10 }),
          event('2026-08-01', { flags: 5 }),
          event('2026-08-02', { flags: 3 }),
        ]),
      )

      expect(result).toEqual([
        { day: '1 Aug', total: 15 },
        { day: '2 Aug', total: 3 },
      ])
    })

    it('orders by date rather than by the formatted label', () => {
      const result = dailyTotals(
        usage([
          event('2026-08-10', { flags: 1 }),
          event('2026-08-02', { flags: 2 }),
          event('2026-09-01', { flags: 3 }),
        ]),
      )

      expect(result.map((point) => point.day)).toEqual([
        '2 Aug',
        '10 Aug',
        '1 Sep',
      ])
    })

    it('treats missing metrics as zero', () => {
      const result = dailyTotals(usage([{ day: '2026-08-01' } as UsageEvent]))

      expect(result).toEqual([{ day: '1 Aug', total: 0 }])
    })

    it('returns nothing when there is no data', () => {
      expect(dailyTotals(undefined)).toEqual([])
      expect(dailyTotals(usage([]))).toEqual([])
    })
  })

  describe('cumulativeTotals', () => {
    it('accumulates across the period', () => {
      const result = cumulativeTotals([
        { day: '1 Aug', total: 10 },
        { day: '2 Aug', total: 5 },
        { day: '3 Aug', total: 0 },
      ])

      expect(result).toEqual([
        { cumulative: 10, day: '1 Aug' },
        { cumulative: 15, day: '2 Aug' },
        { cumulative: 15, day: '3 Aug' },
      ])
    })

    it('returns nothing for an empty period', () => {
      expect(cumulativeTotals([])).toEqual([])
    })
  })

  describe('planLimitThreshold', () => {
    it('labels the ceiling with the shortened limit', () => {
      expect(planLimitThreshold(2000000)).toEqual(
        expect.objectContaining({ label: 'Plan limit · 2M', value: 2000000 }),
      )
    })

    it.each([[null], [undefined], [0]])(
      'has nothing to draw for %p',
      (limit) => {
        expect(planLimitThreshold(limit)).toBeUndefined()
      },
    )
  })

  describe('xAxisIntervalFor', () => {
    it.each`
      points | expected
      ${0}   | ${0}
      ${12}  | ${0}
      ${13}  | ${1}
      ${30}  | ${2}
      ${90}  | ${7}
    `('thins $points points to every $expected', ({ expected, points }) => {
      expect(xAxisIntervalFor(points)).toBe(expected)
    })
  })
})
