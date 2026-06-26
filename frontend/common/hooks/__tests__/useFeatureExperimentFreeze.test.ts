jest.mock('common/services/useExperiment', () => ({
  useGetExperimentsQuery: jest.fn(),
}))

jest.mock('react', () => ({
  ...jest.requireActual('react'),
  useMemo: (fn: () => any) => fn(),
}))

import { useFeatureExperimentFreeze } from 'common/hooks/useFeatureExperimentFreeze'
import { useGetExperimentsQuery } from 'common/services/useExperiment'
import { Experiment } from 'common/types/responses'

const mockUseGetExperimentsQuery =
  useGetExperimentsQuery as jest.MockedFunction<typeof useGetExperimentsQuery>

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
const loading = { data: undefined, isLoading: true } as any

const withResults = (experiments: Experiment[]) =>
  ({ data: { results: experiments }, isLoading: false } as any)

describe('useFeatureExperimentFreeze', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns isFrozen true when a running experiment exists for the feature', () => {
    mockUseGetExperimentsQuery
      .mockReturnValueOnce(
        withResults([makeExperiment({ featureId: 42, status: 'running' })]),
      )
      .mockReturnValueOnce(empty)

    const result = useFeatureExperimentFreeze(42, 'env-123')

    expect(result.isFrozen).toBe(true)
    expect(result.experiment?.id).toBe(1)
    expect(result.isLoading).toBe(false)
  })

  it('returns isFrozen true when a paused experiment exists for the feature', () => {
    mockUseGetExperimentsQuery
      .mockReturnValueOnce(empty)
      .mockReturnValueOnce(
        withResults([makeExperiment({ featureId: 42, status: 'paused' })]),
      )

    const result = useFeatureExperimentFreeze(42, 'env-123')

    expect(result.isFrozen).toBe(true)
  })

  it('returns isFrozen false when no experiments exist', () => {
    mockUseGetExperimentsQuery
      .mockReturnValueOnce(empty)
      .mockReturnValueOnce(empty)

    const result = useFeatureExperimentFreeze(42, 'env-123')

    expect(result.isFrozen).toBe(false)
    expect(result.experiment).toBeNull()
  })

  it('returns isFrozen false when experiment belongs to a different feature', () => {
    mockUseGetExperimentsQuery
      .mockReturnValueOnce(
        withResults([makeExperiment({ featureId: 99, status: 'running' })]),
      )
      .mockReturnValueOnce(empty)

    const result = useFeatureExperimentFreeze(42, 'env-123')

    expect(result.isFrozen).toBe(false)
  })

  it('returns isLoading true while either query is loading', () => {
    mockUseGetExperimentsQuery
      .mockReturnValueOnce(empty)
      .mockReturnValueOnce(loading)

    const result = useFeatureExperimentFreeze(42, 'env-123')

    expect(result.isFrozen).toBe(false)
    expect(result.isLoading).toBe(true)
  })

  it('skips both queries when featureId is undefined', () => {
    mockUseGetExperimentsQuery
      .mockReturnValueOnce(empty)
      .mockReturnValueOnce(empty)

    const result = useFeatureExperimentFreeze(undefined, 'env-123')

    expect(result.isFrozen).toBe(false)
    expect(mockUseGetExperimentsQuery).toHaveBeenCalledTimes(2)
    expect(mockUseGetExperimentsQuery).toHaveBeenNthCalledWith(
      1,
      { environmentId: 'env-123', status: 'running' },
      { skip: true },
    )
    expect(mockUseGetExperimentsQuery).toHaveBeenNthCalledWith(
      2,
      { environmentId: 'env-123', status: 'paused' },
      { skip: true },
    )
  })

  it('passes status filter to each query', () => {
    mockUseGetExperimentsQuery
      .mockReturnValueOnce(empty)
      .mockReturnValueOnce(empty)

    useFeatureExperimentFreeze(42, 'env-123')

    expect(mockUseGetExperimentsQuery).toHaveBeenNthCalledWith(
      1,
      { environmentId: 'env-123', status: 'running' },
      { skip: false },
    )
    expect(mockUseGetExperimentsQuery).toHaveBeenNthCalledWith(
      2,
      { environmentId: 'env-123', status: 'paused' },
      { skip: false },
    )
  })
})
