import { colorChart1 } from 'common/theme/tokens'
import {
  usageEvent,
  usageResponse,
} from 'components/pages/usage/__tests__/fixtures'
import {
  breakdownStatusOf,
  byRequestType,
  byScope,
  groupByOf,
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

  describe('byScope', () => {
    it('ranks projects by their total and names them', () => {
      const rows = byScope(
        usageResponse([
          usageEvent({ flags: 10, project_id: 1 }),
          usageEvent({ flags: 5, identities: 20, project_id: 2 }),
          usageEvent({ flags: 4, project_id: 1 }),
        ]),
        'project_id',
        new Map([
          [1, 'Checkout'],
          [2, 'Mobile app'],
        ]),
        'Deleted project',
      )

      expect(rows.map(({ label, value }) => [label, value])).toEqual([
        ['Mobile app', 25],
        ['Checkout', 14],
      ])
    })

    it('labels usage from a project that no longer exists', () => {
      const rows = byScope(
        usageResponse([usageEvent({ flags: 3, project_id: 9 })]),
        'project_id',
        new Map(),
        'Deleted project',
      )

      expect(rows[0].label).toBe('Deleted project')
    })

    it('skips rows the API did not group', () => {
      expect(
        byScope(
          usageResponse([usageEvent({ flags: 3 })]),
          'environment_id',
          new Map(),
          'Deleted environment',
        ),
      ).toEqual([])
    })
  })

  describe('groupByOf', () => {
    it.each`
      dimension         | projectId    | expected
      ${'request-type'} | ${undefined} | ${undefined}
      ${'sdk'}          | ${12}        | ${undefined}
      ${'project'}      | ${undefined} | ${'project'}
      ${'environment'}  | ${undefined} | ${undefined}
      ${'environment'}  | ${12}        | ${'environment'}
    `(
      '$dimension with project $projectId groups by $expected',
      ({ dimension, expected, projectId }) => {
        expect(groupByOf(dimension, projectId)).toBe(expected)
      },
    )
  })

  describe('breakdownStatusOf', () => {
    const idle = { isError: false, isFetching: false }

    it.each`
      groupBy      | queries                                                 | expected
      ${undefined} | ${[idle]}                                               | ${'needs-project'}
      ${'project'} | ${[idle, { ...idle, isFetching: true }]}                | ${'loading'}
      ${'project'} | ${[{ ...idle, isError: true }, idle]}                   | ${'error'}
      ${'project'} | ${[{ isError: true, isFetching: true }]}                | ${'loading'}
      ${'project'} | ${[{ ...idle, error: { status: 429 }, isError: true }]} | ${'throttled'}
      ${'project'} | ${[{ ...idle, error: { status: 500 }, isError: true }]} | ${'error'}
      ${'project'} | ${[idle, idle]}                                         | ${'ready'}
    `('is $expected', ({ expected, groupBy, queries }) => {
      expect(breakdownStatusOf(groupBy, queries)).toBe(expected)
    })
  })
})
