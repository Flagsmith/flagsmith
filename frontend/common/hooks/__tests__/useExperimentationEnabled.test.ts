jest.mock('common/services/useBuildVersion', () => ({
  useGetBuildVersionQuery: jest.fn(),
}))

import { useExperimentationEnabled } from 'common/hooks/useExperimentationEnabled'
import { useGetBuildVersionQuery } from 'common/services/useBuildVersion'

const mockUseGetBuildVersionQuery =
  useGetBuildVersionQuery as jest.MockedFunction<typeof useGetBuildVersionQuery>

describe('useExperimentationEnabled', () => {
  it.each([
    [true, undefined, { enabled: false, isLoading: true }],
    [false, false, { enabled: false, isLoading: false }],
    [false, true, { enabled: true, isLoading: false }],
  ])(
    'isLoading=%s experimentation_enabled=%s => %j',
    (isLoading, experimentationEnabled, expected) => {
      mockUseGetBuildVersionQuery.mockReturnValue({
        data:
          experimentationEnabled === undefined
            ? undefined
            : { backend: { experimentation_enabled: experimentationEnabled } },
        isLoading,
      } as any)

      expect(useExperimentationEnabled()).toEqual(expected)
    },
  )
})
