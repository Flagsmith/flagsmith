import {
  usageEvent,
  usageResponse,
} from 'components/pages/usage/__tests__/fixtures'
import {
  breakdownStatusOf,
  breakdownViewOf,
  retryFailed,
} from 'components/pages/usage/components/UsageBreakdown/breakdownView'
import {
  byRequestType,
  bySdk,
} from 'components/pages/usage/components/UsageBreakdown/utils'

describe('breakdownView', () => {
  describe('breakdownStatusOf', () => {
    const idle = { isError: false, isFetching: false }

    it.each`
      groupBy      | queries                                                 | expected
      ${undefined} | ${[idle]}                                               | ${'needs-project'}
      ${'project'} | ${[idle, { ...idle, isFetching: true }]}                | ${'loading'}
      ${'project'} | ${[{ ...idle, isError: true }, idle]}                   | ${'error'}
      ${'project'} | ${[{ isError: true, isFetching: true }]}                | ${'loading'}
      ${'project'} | ${[{ ...idle, error: { status: 500 }, isError: true }]} | ${'error'}
      ${'project'} | ${[idle, idle]}                                         | ${'ready'}
    `('is $expected', ({ expected, groupBy, queries }) => {
      expect(breakdownStatusOf(groupBy, queries, true)).toBe(expected)
    })

    it.each([undefined, 'project'] as const)(
      'is loading while the organisation loads, grouped by %s',
      (groupBy) => {
        expect(breakdownStatusOf(groupBy, [idle], false)).toBe('loading')
      },
    )
  })

  describe('breakdownViewOf', () => {
    const data = usageResponse([
      usageEvent({ flags: 10, labels: { user_agent: 'python/3.1.0' } }),
    ])
    const grouped = {
      onRetry: () => {},
      rows: [{ key: 'project_id-1', label: 'Checkout', value: 10 }],
      status: 'ready' as const,
    }

    it.each`
      dimension         | rows
      ${'request-type'} | ${byRequestType(data)}
      ${'sdk'}          | ${bySdk(data)}
    `('reads $dimension from the usage on screen', ({ dimension, rows }) => {
      expect(breakdownViewOf(dimension, data, grouped)).toEqual({ rows })
    })

    it.each(['project', 'environment'] as const)(
      'takes %s from the grouped request',
      (dimension) => {
        expect(breakdownViewOf(dimension, data, grouped)).toBe(grouped)
      },
    )

    it('is loading, not empty, before the grouped request answers', () => {
      expect(breakdownViewOf('project', data, undefined)).toEqual({
        rows: [],
        status: 'loading',
      })
    })
  })

  describe('retryFailed', () => {
    it('refetches only the queries that failed', () => {
      const refetched: string[] = []
      const query = (name: string, isError: boolean) => ({
        isError,
        refetch: () => refetched.push(name),
      })

      retryFailed([
        query('usage', false),
        query('environments', true),
        query('projects', false),
      ])

      expect(refetched).toEqual(['environments'])
    })
  })
})
