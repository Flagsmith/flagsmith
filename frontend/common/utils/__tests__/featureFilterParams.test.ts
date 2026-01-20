// Mock useProjectFlag to avoid deep dependency chain with legacy JS files
jest.mock('common/services/useProjectFlag', () => ({
  FEATURES_PAGE_SIZE: 100,
}))

import {
  buildUrlParams,
  buildApiFilterParams,
  getFiltersFromParams,
  hasActiveFilters,
} from 'common/utils/featureFilterParams'
import { SortOrder } from 'common/types/requests'
import { TagStrategy } from 'common/types/responses'
import type { FilterState } from 'common/types/featureFilters'

const createDefaultFilters = (
  overrides?: Partial<FilterState>,
): FilterState => ({
  group_owners: [],
  is_enabled: null,
  owners: [],
  search: null,
  showArchived: false,
  sort: {
    label: 'Name',
    sortBy: 'name',
    sortOrder: SortOrder.ASC,
  },
  tag_strategy: TagStrategy.INTERSECTION,
  tags: [],
  value_search: '',
  ...overrides,
})

describe('featureFilterParams', () => {
  describe('buildUrlParams', () => {
    it.each`
      showArchived | expected
      ${false}     | ${'false'}
      ${true}      | ${'true'}
    `(
      'sets is_archived to "$expected" when showArchived is $showArchived',
      ({ expected, showArchived }) => {
        const result = buildUrlParams(createDefaultFilters({ showArchived }), 1)
        expect(result.is_archived).toBe(expected)
      },
    )

    it('always includes is_archived (never undefined)', () => {
      const result = buildUrlParams(createDefaultFilters(), 1)
      expect(result.is_archived).toBeDefined()
    })

    it('includes page number', () => {
      const result = buildUrlParams(createDefaultFilters(), 5)
      expect(result.page).toBe(5)
    })

    it('includes sort parameters', () => {
      const filters = createDefaultFilters({
        sort: {
          label: 'Created',
          sortBy: 'created_date',
          sortOrder: SortOrder.DESC,
        },
      })
      const result = buildUrlParams(filters, 1)
      expect(result.sortBy).toBe('created_date')
      expect(result.sortOrder).toBe('desc')
    })

    it('includes tags when present', () => {
      const result = buildUrlParams(
        createDefaultFilters({ tags: [1, 2, 3] }),
        1,
      )
      expect(result.tags).toBe('1,2,3')
    })

    it('excludes empty arrays and search', () => {
      const filters = createDefaultFilters({ owners: [], search: '', tags: [] })
      const result = buildUrlParams(filters, 1)
      expect(result.tags).toBeUndefined()
      expect(result.owners).toBeUndefined()
      expect(result.search).toBeUndefined()
    })

    it('includes search when present', () => {
      const result = buildUrlParams(createDefaultFilters({ search: 'test' }), 1)
      expect(result.search).toBe('test')
    })
  })

  describe('buildApiFilterParams', () => {
    const mockResolver = (apiKey: string) =>
      apiKey === 'test-key' ? 123 : undefined

    it.each`
      showArchived | expected
      ${false}     | ${'false'}
      ${true}      | ${'true'}
    `(
      'sets is_archived to "$expected" when showArchived is $showArchived',
      ({ expected, showArchived }) => {
        const result = buildApiFilterParams(
          createDefaultFilters({ showArchived }),
          1,
          'test-key',
          1,
          mockResolver,
        )
        expect(result?.is_archived).toBe(expected)
      },
    )

    it('always includes is_archived (never undefined)', () => {
      const result = buildApiFilterParams(
        createDefaultFilters(),
        1,
        'test-key',
        1,
        mockResolver,
      )
      expect(result).not.toBeNull()
      expect(result?.is_archived).toBeDefined()
    })

    it('returns null when environment ID cannot be resolved', () => {
      const result = buildApiFilterParams(
        createDefaultFilters(),
        1,
        'invalid-key',
        1,
        mockResolver,
      )
      expect(result).toBeNull()
    })

    it('includes environmentId and projectId', () => {
      const result = buildApiFilterParams(
        createDefaultFilters(),
        1,
        'test-key',
        42,
        mockResolver,
      )
      expect(result?.environmentId).toBe('123')
      expect(result?.projectId).toBe(42)
    })
  })

  describe('getFiltersFromParams', () => {
    it.each`
      is_archived  | expected
      ${'true'}    | ${true}
      ${'false'}   | ${false}
      ${undefined} | ${false}
    `(
      'parses is_archived=$is_archived to showArchived=$expected',
      ({ expected, is_archived }) => {
        const result = getFiltersFromParams(is_archived ? { is_archived } : {})
        expect(result.showArchived).toBe(expected)
      },
    )

    it.each`
      page         | expected
      ${'3'}       | ${3}
      ${undefined} | ${1}
    `('parses page=$page to $expected', ({ expected, page }) => {
      const result = getFiltersFromParams(page ? { page } : {})
      expect(result.page).toBe(expected)
    })

    it('parses tags as array of numbers', () => {
      const result = getFiltersFromParams({ tags: '1,2,3' })
      expect(result.tags).toEqual([1, 2, 3])
    })

    it('parses sort order', () => {
      const result = getFiltersFromParams({
        sortBy: 'created_date',
        sortOrder: 'desc',
      })
      expect(result.sort.sortBy).toBe('created_date')
      expect(result.sort.sortOrder).toBe(SortOrder.DESC)
    })
  })

  describe('hasActiveFilters', () => {
    it('returns false for default filters', () => {
      expect(hasActiveFilters(createDefaultFilters())).toBe(false)
    })

    it.each`
      scenario            | overrides
      ${'tags present'}   | ${{ tags: [1] }}
      ${'showArchived'}   | ${{ showArchived: true }}
      ${'search present'} | ${{ search: 'test' }}
      ${'is_enabled set'} | ${{ is_enabled: true }}
      ${'owners present'} | ${{ owners: [1] }}
    `('returns true when $scenario', ({ overrides }) => {
      expect(hasActiveFilters(createDefaultFilters(overrides))).toBe(true)
    })
  })
})
