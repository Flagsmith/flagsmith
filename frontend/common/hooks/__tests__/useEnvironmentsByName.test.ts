import { skipToken } from '@reduxjs/toolkit/query'
import { useEnvironmentsByName } from 'common/hooks/useEnvironmentsByName'
import { makeEnvironment } from 'common/utils/__tests__/environmentFixture'

const mockQuery = jest.fn()

jest.mock('common/services/useEnvironment', () => ({
  useGetEnvironmentsQuery: (args: unknown) => mockQuery(args),
}))

jest.mock('react', () => ({
  ...jest.requireActual('react'),
  useMemo: (fn: () => unknown) => fn(),
}))

describe('useEnvironmentsByName', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('sorts the environments by name', () => {
    // Given
    mockQuery.mockReturnValue({
      data: {
        results: [
          makeEnvironment(1, 'Production'),
          makeEnvironment(2, 'Development'),
          makeEnvironment(3, 'Staging'),
        ],
      },
      isError: false,
      isLoading: false,
    })

    // When
    const { environments } = useEnvironmentsByName(1)

    // Then
    expect(environments?.map((env) => env.name)).toEqual([
      'Development',
      'Production',
      'Staging',
    ])
  })

  it('returns no environments while loading', () => {
    // Given
    mockQuery.mockReturnValue({ isError: false, isLoading: true })

    // When
    const result = useEnvironmentsByName(1)

    // Then
    expect(result).toEqual({
      environments: undefined,
      isError: false,
      isLoading: true,
    })
  })

  it('passes the error through', () => {
    // Given
    mockQuery.mockReturnValue({ isError: true, isLoading: false })

    // When
    const result = useEnvironmentsByName(1)

    // Then
    expect(result.isError).toBe(true)
    expect(result.environments).toBeUndefined()
  })

  it('skips the request without a project', () => {
    // Given
    mockQuery.mockReturnValue({ isError: false, isLoading: false })

    // When
    useEnvironmentsByName(undefined)

    // Then
    expect(mockQuery).toHaveBeenCalledWith(skipToken)
  })
})
