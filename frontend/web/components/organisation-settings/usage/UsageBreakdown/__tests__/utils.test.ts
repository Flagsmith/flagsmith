import { Res, UsageEventsList } from 'common/types/responses'
import {
  byRequestType,
  bySdk,
  fromScopedTotals,
  totalOf,
} from 'components/organisation-settings/usage/UsageBreakdown/utils'

const event = (values: Partial<UsageEventsList> = {}): UsageEventsList =>
  ({
    day: '2026-08-01',
    environment_document: 0,
    flags: 0,
    identities: 0,
    labels: { user_agent: null },
    traits: 0,
    ...values,
  } as UsageEventsList)

const usage = (events: UsageEventsList[]) =>
  ({ events_list: events } as Res['organisationUsage'])

describe('UsageBreakdown utils', () => {
  describe('totalOf', () => {
    it('counts every billable type', () => {
      expect(
        totalOf(
          event({
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
    it('sums each type across every day, biggest first', () => {
      const result = byRequestType(
        usage([
          event({ flags: 10, identities: 2 }),
          event({ flags: 5, traits: 20 }),
        ]),
      )

      expect(result).toEqual([
        { label: 'Traits', value: 20 },
        { label: 'Flags', value: 15 },
        { label: 'Identities', value: 2 },
      ])
    })

    it('drops types with no usage rather than showing empty rows', () => {
      const result = byRequestType(usage([event({ flags: 3 })]))

      expect(result).toEqual([{ label: 'Flags', value: 3 }])
    })

    it('returns nothing when there is no data', () => {
      expect(byRequestType(undefined)).toEqual([])
      expect(byRequestType(usage([]))).toEqual([])
    })
  })

  describe('bySdk', () => {
    it('groups by user agent, biggest first', () => {
      const result = bySdk(
        usage([
          event({ flags: 10, labels: { user_agent: 'python/3.1.0' } }),
          event({ flags: 4, labels: { user_agent: 'java/2.0.0' } }),
          event({ identities: 5, labels: { user_agent: 'python/3.1.0' } }),
        ]),
      )

      expect(result).toEqual([
        { label: 'python/3.1.0', value: 15 },
        { label: 'java/2.0.0', value: 4 },
      ])
    })

    // Older events predate user-agent capture. Dropping them would make the
    // rows disagree with the total on the meter above.
    it('keeps unattributed usage rather than dropping it', () => {
      const result = bySdk(
        usage([
          event({ flags: 10, labels: { user_agent: null } }),
          event({ flags: 4, labels: { user_agent: 'go/1.0.0' } }),
        ]),
      )

      expect(result).toEqual([
        { label: 'Unknown', value: 10 },
        { label: 'go/1.0.0', value: 4 },
      ])
    })

    it('returns nothing when there is no data', () => {
      expect(bySdk(undefined)).toEqual([])
    })
  })

  describe('fromScopedTotals', () => {
    it('ranks one row per scope', () => {
      const result = fromScopedTotals([
        {
          data: { totals: { total: 40 } } as Res['organisationUsage'],
          label: 'Project A',
        },
        {
          data: { totals: { total: 90 } } as Res['organisationUsage'],
          label: 'Project B',
        },
      ])

      expect(result).toEqual([
        { label: 'Project B', value: 90 },
        { label: 'Project A', value: 40 },
      ])
    })

    it('skips scopes that have not loaded or have no usage', () => {
      const result = fromScopedTotals([
        { data: undefined, label: 'Still loading' },
        {
          data: { totals: { total: 0 } } as Res['organisationUsage'],
          label: 'Idle',
        },
        {
          data: { totals: { total: 7 } } as Res['organisationUsage'],
          label: 'Busy',
        },
      ])

      expect(result).toEqual([{ label: 'Busy', value: 7 }])
    })
  })
})
