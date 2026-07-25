jest.mock('common/services/useExperiment', () => ({
  useGetExperimentsQuery: jest.fn(),
}))

jest.mock('react', () => ({
  ...jest.requireActual('react'),
  useMemo: (fn: () => any) => fn(),
}))

jest.mock('common/utils/utils', () => ({
  __esModule: true,
  default: {
    getFlagsmithHasFeature: jest.fn(),
  },
}))

import { useFeatureExperimentFreeze } from 'common/hooks/useFeatureExperimentFreeze'
import { useGetExperimentsQuery } from 'common/services/useExperiment'
import Utils from 'common/utils/utils'
import { Experiment } from 'common/types/responses'

const mockUseGetExperimentsQuery =
  useGetExperimentsQuery as jest.MockedFunction<typeof useGetExperimentsQuery>
const mockGetFlagsmithHasFeature =
  Utils.getFlagsmithHasFeature as jest.MockedFunction<
    typeof Utils.getFlagsmithHasFeature
  >

const makeExperiment = (
  overrides: Partial<Experiment> & { featureId: number },
): Experiment => ({
  created_at: '',
  ended_at: null,
  feature: {
    id: overrides.featureId,
    initial_value: null,
    multivariate_options: [],
    name: 'test-flag',
    type: 'MULTIVARIATE',
  },
  hypothesis: '',
  id: 1,
  metrics: [],
  name: 'Test Experiment',
  started_at: null,
  status: overrides.status ?? 'running',
  updated_at: '',
  ...overrides,
})

const empty = { data: { results: [] }, isLoading: false } as any

const withResults = (experiments: Experiment[]) =>
  ({ data: { results: experiments }, isLoading: false } as any)

describe('useFeatureExperimentFreeze', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockGetFlagsmithHasFeature.mockReturnValue(true)
  })

  it('returns isFrozen true when a running experiment exists for the feature', () => {
    mockUseGetExperimentsQuery.mockReturnValue(
      withResults([makeExperiment({ featureId: 42, status: 'running' })]),
    )

    const result = useFeatureExperimentFreeze(42, 'env-123')

    expect(result.isFrozen).toBe(true)
    expect(result.experiment?.id).toBe(1)
  })

  it('returns isFrozen false when no experiments exist', () => {
    mockUseGetExperimentsQuery.mockReturnValue(empty)

    const result = useFeatureExperimentFreeze(42, 'env-123')

    expect(result.isFrozen).toBe(false)
    expect(result.experiment).toBeNull()
  })

  it('returns isFrozen false when experiment belongs to a different feature', () => {
    mockUseGetExperimentsQuery.mockReturnValue(
      withResults([makeExperiment({ featureId: 99, status: 'running' })]),
    )

    const result = useFeatureExperimentFreeze(42, 'env-123')

    expect(result.isFrozen).toBe(false)
  })

  it('returns isLoading true while the query is loading', () => {
    mockUseGetExperimentsQuery.mockReturnValue({
      data: undefined,
      isLoading: true,
    } as any)

    const result = useFeatureExperimentFreeze(42, 'env-123')

    expect(result.isFrozen).toBe(false)
    expect(result.isLoading).toBe(true)
  })

  it('skips query when featureId is undefined', () => {
    mockUseGetExperimentsQuery.mockReturnValue(empty)

    const result = useFeatureExperimentFreeze(undefined, 'env-123')

    expect(result.isFrozen).toBe(false)
    expect(mockUseGetExperimentsQuery).toHaveBeenCalledWith(
      { environmentId: 'env-123', status: 'running' },
      { skip: true },
    )
  })

  it('skips query when environmentId is empty', () => {
    mockUseGetExperimentsQuery.mockReturnValue(empty)

    const result = useFeatureExperimentFreeze(42, '')

    expect(result.isFrozen).toBe(false)
    expect(mockUseGetExperimentsQuery).toHaveBeenCalledWith(
      { environmentId: '', status: 'running' },
      { skip: true },
    )
  })

  it('skips query when experimental_flags feature is disabled', () => {
    mockGetFlagsmithHasFeature.mockReturnValue(false)
    mockUseGetExperimentsQuery.mockReturnValue(empty)

    const result = useFeatureExperimentFreeze(42, 'env-123')

    expect(result.isFrozen).toBe(false)
    expect(mockUseGetExperimentsQuery).toHaveBeenCalledWith(
      { environmentId: 'env-123', status: 'running' },
      { skip: true },
    )
  })

  it('queries only running experiments when feature is enabled', () => {
    mockUseGetExperimentsQuery.mockReturnValue(empty)

    useFeatureExperimentFreeze(42, 'env-123')

    expect(mockUseGetExperimentsQuery).toHaveBeenCalledTimes(1)
    expect(mockUseGetExperimentsQuery).toHaveBeenCalledWith(
      { environmentId: 'env-123', status: 'running' },
      { skip: false },
    )
  })
})
