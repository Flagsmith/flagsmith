import { colorChart1 } from 'common/theme/tokens'
import {
  usageEvent,
  usageResponse,
} from 'components/pages/usage/__tests__/fixtures'
import {
  byRequestType,
  barPercent,
  bySdk,
  sharesOf,
  totalOf,
} from 'components/pages/usage/components/UsageBreakdown/utils'

describe('UsageBreakdown utils', () => {
  describe('totalOf', () => {
    it('counts every billable type', () => {
      expect(
        totalOf(
          usageEvent({
            environment_document: 1,
            flags: 10,
            identities: 5,
            traits: 2,
          }),
        ),
      ).toBe(18)
    })
  })

  describe('byRequestType', () => {
    it('carries the colour each type has always had on the usage page', () => {
      const result = byRequestType(usageResponse([usageEvent({ flags: 1 })]))

      expect(result[0].colour).toBe(colorChart1)
    })

    it('sums each type across every day, biggest first', () => {
      const result = byRequestType(
        usageResponse([
          usageEvent({ flags: 10, identities: 2 }),
          usageEvent({ flags: 5, traits: 20 }),
        ]),
      )

      expect(
        result.map(({ key, label, value }) => ({ key, label, value })),
      ).toEqual([
        { key: 'traits', label: 'Traits', value: 20 },
        { key: 'flags', label: 'Flags', value: 15 },
        { key: 'identities', label: 'Identities', value: 2 },
      ])
    })

    it('drops types with no usage rather than showing empty rows', () => {
      const result = byRequestType(usageResponse([usageEvent({ flags: 3 })]))

      expect(result.map(({ label, value }) => ({ label, value }))).toEqual([
        { label: 'Flags', value: 3 },
      ])
    })

    it('returns nothing when there is no data', () => {
      expect(byRequestType(undefined)).toEqual([])
      expect(byRequestType(usageResponse([]))).toEqual([])
    })
  })

  describe('bySdk', () => {
    it('groups by user agent, biggest first', () => {
      const result = bySdk(
        usageResponse([
          usageEvent({ flags: 10, labels: { user_agent: 'python/3.1.0' } }),
          usageEvent({ flags: 4, labels: { user_agent: 'java/2.0.0' } }),
          usageEvent({ identities: 5, labels: { user_agent: 'python/3.1.0' } }),
        ]),
      )

      expect(result.map(({ label, value }) => ({ label, value }))).toEqual([
        { label: 'python/3.1.0', value: 15 },
        { label: 'java/2.0.0', value: 4 },
      ])
    })

    // Older events predate user-agent capture. Dropping them would make the
    // rows disagree with the total on the meter above.
    it('keeps unattributed usage rather than dropping it', () => {
      const result = bySdk(
        usageResponse([
          usageEvent({ flags: 10, labels: { user_agent: null } }),
          usageEvent({ flags: 4, labels: { user_agent: 'go/1.0.0' } }),
        ]),
      )

      expect(result.map(({ label, value }) => ({ label, value }))).toEqual([
        { label: 'Unknown', value: 10 },
        { label: 'go/1.0.0', value: 4 },
      ])
    })

    it('returns nothing when there is no data', () => {
      expect(bySdk(undefined)).toEqual([])
    })
  })

  describe('sharesOf', () => {
    it('adds up to 100 when the split does not divide evenly', () => {
      const shares = sharesOf([1, 1, 1])

      expect(shares.reduce((sum, share) => sum + share, 0)).toBe(100)
      expect(shares).toEqual([34, 33, 33])
    })

    it('gives the spare points to the largest remainders', () => {
      const shares = sharesOf([5, 3, 1])

      expect(shares.reduce((sum, share) => sum + share, 0)).toBe(100)
    })

    it('reports zero rather than NaN when nothing was used', () => {
      expect(sharesOf([0, 0])).toEqual([0, 0])
    })
  })

  describe('barPercent', () => {
    it('keeps a tiny contributor visible rather than rounding it away', () => {
      expect(barPercent(9_000, 8_900_000)).toBe(1)
    })

    it('scales to the largest row', () => {
      expect(barPercent(4_450_000, 8_900_000)).toBe(50)
      expect(barPercent(8_900_000, 8_900_000)).toBe(100)
    })

    it('draws nothing when there is nothing to draw', () => {
      expect(barPercent(0, 8_900_000)).toBe(0)
      expect(barPercent(10, 0)).toBe(0)
    })
  })
})
