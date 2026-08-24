import { colorChart1 } from 'common/theme/tokens'
import {
  usageEvent,
  usageResponse,
} from 'components/pages/usage/__tests__/fixtures'
import {
  byRequestType,
  bySdk,
  fromScopedTotals,
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

  describe('fromScopedTotals', () => {
    const scopes = [
      { key: 'project-1', label: 'Project A' },
      { key: 'project-2', label: 'Project B' },
    ]

    it('ranks one row per scope', () => {
      const result = fromScopedTotals(scopes, {
        'project-1': 40,
        'project-2': 90,
      })

      expect(result).toEqual([
        { key: 'project-2', label: 'Project B', value: 90 },
        { key: 'project-1', label: 'Project A', value: 40 },
      ])
    })

    // Two projects can share a name, so rows key on the scope rather than it.
    it('keeps same-named scopes apart', () => {
      const result = fromScopedTotals(
        [
          { key: 'project-1', label: 'Checkout' },
          { key: 'project-2', label: 'Checkout' },
        ],
        { 'project-1': 10, 'project-2': 25 },
      )

      expect(result.map((row) => row.value)).toEqual([25, 10])
    })

    it('skips scopes with no usage or none reported yet', () => {
      const result = fromScopedTotals(
        [...scopes, { key: 'project-3', label: 'Idle' }],
        { 'project-1': 7, 'project-3': 0 },
      )

      expect(result).toEqual([
        { key: 'project-1', label: 'Project A', value: 7 },
      ])
    })
  })
})
