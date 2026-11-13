import { skipToken } from '@reduxjs/toolkit/query'
import { useSortedProjectEnvironments } from 'common/hooks/useSortedProjectEnvironments'
import { makeEnvironment } from 'common/utils/__tests__/environmentFixture'

const mockQuery = jest.fn()

jest.mock('common/services/useEnvironment', () => ({
  useGetAllEnvironmentsQuery: (args: unknown) => mockQuery(args),
}))

jest.mock('react', () => ({
  ...jest.requireActual('react'),
  useMemo: (fn: () => unknown) => fn(),
}))

const previousProjectEnvironments = [makeEnvironment(9, 'Other project env')]

describe('useSortedProjectEnvironments', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('sorts the environments by name', () => {
    // Given
    mockQuery.mockReturnValue({
      currentData: [
        makeEnvironment(1, 'Production'),
        makeEnvironment(2, 'Development'),
        makeEnvironment(3, 'Staging'),
      ],
      isError: false,
      isFetching: false,
    })

    // When
    const { environments } = useSortedProjectEnvironments(1)

    // Then
    expect(environments?.map((env) => env.name)).toEqual([
      'Development',
      'Production',
      'Staging',
    ])
  })

  it('returns no environments while loading', () => {
    // Given
    mockQuery.mockReturnValue({ isError: false, isFetching: true })

    // When
    const result = useSortedProjectEnvironments(1)

    // Then
    expect(result).toEqual({
      environments: undefined,
      isError: false,
      isLoading: true,
    })
  })

  it('drops the previous project while the next one loads', () => {
    // Given RTK Query keeps the last result in data after the argument changes
    mockQuery.mockReturnValue({
      currentData: undefined,
      data: previousProjectEnvironments,
      isError: false,
      isFetching: true,
    })

    // When
    const result = useSortedProjectEnvironments(2)

    // Then
    expect(result).toEqual({
      environments: undefined,
      isError: false,
      isLoading: true,
    })
  })

  it('drops the previous project when the next one fails', () => {
    // Given
    mockQuery.mockReturnValue({
      currentData: undefined,
      data: previousProjectEnvironments,
      isError: true,
      isFetching: false,
    })

    // When
    const result = useSortedProjectEnvironments(2)

    // Then
    expect(result).toEqual({
      environments: undefined,
      isError: true,
      isLoading: false,
    })
  })

  it('skips the request without a project', () => {
    // Given
    mockQuery.mockReturnValue({ isError: false, isFetching: false })

    // When
    useSortedProjectEnvironments(undefined)

    // Then
    expect(mockQuery).toHaveBeenCalledWith(skipToken)
  })
})
