jest.mock('common/services/useProjectFlag', () => ({
  useGetProjectFlagsQuery: jest.fn(),
}))

jest.mock('common/hooks/useProjectEnvironments', () => ({
  useProjectEnvironments: jest.fn(),
}))

import { useFeatureStates } from 'common/hooks/useFeatureStates'
import { useGetProjectFlagsQuery } from 'common/services/useProjectFlag'
import { useProjectEnvironments } from 'common/hooks/useProjectEnvironments'
import { ProjectFlag } from 'common/types/responses'

const mockUseGetProjectFlagsQuery =
  useGetProjectFlagsQuery as jest.MockedFunction<typeof useGetProjectFlagsQuery>
const mockUseProjectEnvironments =
  useProjectEnvironments as jest.MockedFunction<typeof useProjectEnvironments>

const enabledFeature = {
  environment_feature_state: { enabled: true },
  id: 1,
} as unknown as ProjectFlag

describe('useFeatureStates', () => {
  beforeEach(() => {
    mockUseProjectEnvironments.mockReturnValue({
      error: undefined,
      getEnvironmentIdFromKey: () => 2,
      isLoading: false,
    } as any)
  })

  it("ignores another environment's list while this one's loads", () => {
    // Given
    mockUseGetProjectFlagsQuery.mockReturnValue({
      currentData: undefined,
      data: { results: [enabledFeature] },
      isError: false,
      isLoading: false,
    } as any)

    // When
    const states = useFeatureStates({ environmentId: 'key', projectId: 1 })

    // Then
    expect(states.isLoading).toBe(true)
    expect(states.features).toEqual([])
  })

  it('reads every page of the feature list for the environment', () => {
    // Given
    mockUseGetProjectFlagsQuery.mockReturnValue({
      currentData: { results: [] },
      isError: false,
      isLoading: false,
    } as any)

    // When
    useFeatureStates({ environmentId: 'key', projectId: 1 })

    // Then
    expect(mockUseGetProjectFlagsQuery).toHaveBeenCalledWith(
      { environment: 2, project: '1' },
      { skip: false },
    )
  })

  it("reads this environment's list once loaded", () => {
    // Given
    mockUseGetProjectFlagsQuery.mockReturnValue({
      currentData: { results: [enabledFeature] },
      isError: false,
      isLoading: false,
    } as any)

    // When
    const states = useFeatureStates({ environmentId: 'key', projectId: 1 })

    // Then
    expect(states.isLoading).toBe(false)
    expect(states.isEnabled(1)).toBe(true)
  })
})
