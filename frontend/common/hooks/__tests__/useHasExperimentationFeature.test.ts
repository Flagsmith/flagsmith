jest.mock('common/services/useBuildVersion', () => ({
  useGetBuildVersionQuery: jest.fn(),
}))

jest.mock('common/utils/utils', () => ({
  __esModule: true,
  default: {
    getFlagsmithHasFeature: jest.fn(),
  },
}))

import { useHasExperimentationFeature } from 'common/hooks/useHasExperimentationFeature'
import { useGetBuildVersionQuery } from 'common/services/useBuildVersion'
import Utils from 'common/utils/utils'

const mockUseGetBuildVersionQuery =
  useGetBuildVersionQuery as jest.MockedFunction<typeof useGetBuildVersionQuery>
const mockGetFlagsmithHasFeature =
  Utils.getFlagsmithHasFeature as jest.MockedFunction<
    typeof Utils.getFlagsmithHasFeature
  >

describe('useHasExperimentationFeature', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockGetFlagsmithHasFeature.mockReturnValue(true)
  })

  it('reports loading while the build version is pending', () => {
    mockUseGetBuildVersionQuery.mockReturnValue({
      data: undefined,
      isLoading: true,
    } as any)

    const result = useHasExperimentationFeature('experimental_flags')

    expect(result).toEqual({ enabled: false, isLoading: true })
  })

  it('is disabled when the experimentation infra is not deployed', () => {
    mockUseGetBuildVersionQuery.mockReturnValue({
      data: { backend: { experimentation_enabled: false } },
      isLoading: false,
    } as any)

    const result = useHasExperimentationFeature('experimental_flags')

    expect(result).toEqual({ enabled: false, isLoading: false })
  })

  it('is enabled when the flag is on and the experimentation infra is deployed', () => {
    mockUseGetBuildVersionQuery.mockReturnValue({
      data: { backend: { experimentation_enabled: true } },
      isLoading: false,
    } as any)

    const result = useHasExperimentationFeature('experimental_flags')

    expect(result).toEqual({ enabled: true, isLoading: false })
  })
})
