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
    it('should set is_archived to "false" when showArchived is false', () => {
      const filters = createDefaultFilters({ showArchived: false })
      const result = buildUrlParams(filters, 1)
      expect(result.is_archived).toBe('false')
    })

    it('should set is_archived to "true" when showArchived is true', () => {
      const filters = createDefaultFilters({ showArchived: true })
      const result = buildUrlParams(filters, 1)
      expect(result.is_archived).toBe('true')
    })

    it('should always include is_archived (never undefined)', () => {
      const filters = createDefaultFilters()
      const result = buildUrlParams(filters, 1)
      expect(result.is_archived).toBeDefined()
      expect(result.is_archived).not.toBeUndefined()
    })

    it('should include page number', () => {
      const filters = createDefaultFilters()
      const result = buildUrlParams(filters, 5)
      expect(result.page).toBe(5)
    })

    it('should include sort parameters', () => {
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

    it('should include tags when present', () => {
      const filters = createDefaultFilters({ tags: [1, 2, 3] })
      const result = buildUrlParams(filters, 1)
      expect(result.tags).toBe('1,2,3')
    })

    it('should exclude empty arrays', () => {
      const filters = createDefaultFilters({ owners: [], tags: [] })
      const result = buildUrlParams(filters, 1)
      expect(result.tags).toBeUndefined()
      expect(result.owners).toBeUndefined()
    })

    it('should include search when present', () => {
      const filters = createDefaultFilters({ search: 'test' })
      const result = buildUrlParams(filters, 1)
      expect(result.search).toBe('test')
    })

    it('should exclude empty search', () => {
      const filters = createDefaultFilters({ search: '' })
      const result = buildUrlParams(filters, 1)
      expect(result.search).toBeUndefined()
    })
  })

  describe('buildApiFilterParams', () => {
    const mockResolver = (apiKey: string) =>
      apiKey === 'test-key' ? 123 : undefined

    it('should set is_archived to "false" when showArchived is false', () => {
      const filters = createDefaultFilters({ showArchived: false })
      const result = buildApiFilterParams(
        filters,
        1,
        'test-key',
        1,
        mockResolver,
      )
      expect(result?.is_archived).toBe('false')
    })

    it('should set is_archived to "true" when showArchived is true', () => {
      const filters = createDefaultFilters({ showArchived: true })
      const result = buildApiFilterParams(
        filters,
        1,
        'test-key',
        1,
        mockResolver,
      )
      expect(result?.is_archived).toBe('true')
    })

    it('should always include is_archived in params (never undefined)', () => {
      const filters = createDefaultFilters()
      const result = buildApiFilterParams(
        filters,
        1,
        'test-key',
        1,
        mockResolver,
      )
      expect(result).not.toBeNull()
      expect(result?.is_archived).toBeDefined()
      expect(result?.is_archived).toBe('false')
    })

    it('should return null when environment ID cannot be resolved', () => {
      const filters = createDefaultFilters()
      const result = buildApiFilterParams(
        filters,
        1,
        'invalid-key',
        1,
        mockResolver,
      )
      expect(result).toBeNull()
    })

    it('should include environmentId and projectId', () => {
      const filters = createDefaultFilters()
      const result = buildApiFilterParams(
        filters,
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
    it('should parse is_archived=true to showArchived=true', () => {
      const params = { is_archived: 'true' }
      const result = getFiltersFromParams(params)
      expect(result.showArchived).toBe(true)
    })

    it('should parse is_archived=false to showArchived=false', () => {
      const params = { is_archived: 'false' }
      const result = getFiltersFromParams(params)
      expect(result.showArchived).toBe(false)
    })

    it('should default showArchived to false when is_archived is not present', () => {
      const params = {}
      const result = getFiltersFromParams(params)
      expect(result.showArchived).toBe(false)
    })

    it('should parse page number', () => {
      const params = { page: '3' }
      const result = getFiltersFromParams(params)
      expect(result.page).toBe(3)
    })

    it('should default page to 1 when not present', () => {
      const params = {}
      const result = getFiltersFromParams(params)
      expect(result.page).toBe(1)
    })

    it('should parse tags as array of numbers', () => {
      const params = { tags: '1,2,3' }
      const result = getFiltersFromParams(params)
      expect(result.tags).toEqual([1, 2, 3])
    })

    it('should parse sort order', () => {
      const params = { sortBy: 'created_date', sortOrder: 'desc' }
      const result = getFiltersFromParams(params)
      expect(result.sort.sortBy).toBe('created_date')
      expect(result.sort.sortOrder).toBe(SortOrder.DESC)
    })
  })

  describe('hasActiveFilters', () => {
    it('should return false for default filters', () => {
      const filters = createDefaultFilters()
      expect(hasActiveFilters(filters)).toBe(false)
    })

    it('should return true when tags are present', () => {
      const filters = createDefaultFilters({ tags: [1] })
      expect(hasActiveFilters(filters)).toBe(true)
    })

    it('should return true when showArchived is true', () => {
      const filters = createDefaultFilters({ showArchived: true })
      expect(hasActiveFilters(filters)).toBe(true)
    })

    it('should return true when search is present', () => {
      const filters = createDefaultFilters({ search: 'test' })
      expect(hasActiveFilters(filters)).toBe(true)
    })

    it('should return true when is_enabled is set', () => {
      const filters = createDefaultFilters({ is_enabled: true })
      expect(hasActiveFilters(filters)).toBe(true)
    })

    it('should return true when owners are present', () => {
      const filters = createDefaultFilters({ owners: [1] })
      expect(hasActiveFilters(filters)).toBe(true)
    })
  })
})
