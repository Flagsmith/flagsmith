jest.mock('common/services/useProjectFlag', () => ({
  useGetFeatureListQuery: jest.fn(),
}))

jest.mock('common/hooks/useProjectEnvironments', () => ({
  useProjectEnvironments: jest.fn(),
}))

import { useFeatureStates } from 'common/hooks/useFeatureStates'
import { useGetFeatureListQuery } from 'common/services/useProjectFlag'
import { useProjectEnvironments } from 'common/hooks/useProjectEnvironments'
import { ProjectFlag } from 'common/types/responses'

const mockUseGetFeatureListQuery =
  useGetFeatureListQuery as jest.MockedFunction<typeof useGetFeatureListQuery>
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
    mockUseGetFeatureListQuery.mockReturnValue({
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

  it("reads this environment's list once loaded", () => {
    // Given
    mockUseGetFeatureListQuery.mockReturnValue({
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
