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

describe('useFeatureExperimentFreeze', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns isFrozen true when a running experiment exists for the feature', () => {
    mockUseGetExperimentsQuery.mockReturnValue({
      data: {
        results: [makeExperiment({ featureId: 42, status: 'running' })],
      },
      isLoading: false,
    } as any)

    const result = useFeatureExperimentFreeze(42, 'env-123')

    expect(result.isFrozen).toBe(true)
    expect(result.experiment?.id).toBe(1)
    expect(result.isLoading).toBe(false)
  })

  it('returns isFrozen true when a paused experiment exists for the feature', () => {
    mockUseGetExperimentsQuery.mockReturnValue({
      data: {
        results: [makeExperiment({ featureId: 42, status: 'paused' })],
      },
      isLoading: false,
    } as any)

    const result = useFeatureExperimentFreeze(42, 'env-123')

    expect(result.isFrozen).toBe(true)
  })

  it('returns isFrozen false when experiment is created (not yet started)', () => {
    mockUseGetExperimentsQuery.mockReturnValue({
      data: {
        results: [makeExperiment({ featureId: 42, status: 'created' })],
      },
      isLoading: false,
    } as any)

    const result = useFeatureExperimentFreeze(42, 'env-123')

    expect(result.isFrozen).toBe(false)
    expect(result.experiment).toBeNull()
  })

  it('returns isFrozen false when experiment is completed', () => {
    mockUseGetExperimentsQuery.mockReturnValue({
      data: {
        results: [makeExperiment({ featureId: 42, status: 'completed' })],
      },
      isLoading: false,
    } as any)

    const result = useFeatureExperimentFreeze(42, 'env-123')

    expect(result.isFrozen).toBe(false)
    expect(result.experiment).toBeNull()
  })

  it('returns isFrozen false when no experiments exist', () => {
    mockUseGetExperimentsQuery.mockReturnValue({
      data: { results: [] },
      isLoading: false,
    } as any)

    const result = useFeatureExperimentFreeze(42, 'env-123')

    expect(result.isFrozen).toBe(false)
    expect(result.experiment).toBeNull()
  })

  it('returns isFrozen false when experiment belongs to a different feature', () => {
    mockUseGetExperimentsQuery.mockReturnValue({
      data: {
        results: [makeExperiment({ featureId: 99, status: 'running' })],
      },
      isLoading: false,
    } as any)

    const result = useFeatureExperimentFreeze(42, 'env-123')

    expect(result.isFrozen).toBe(false)
  })

  it('returns isLoading true while experiments are loading', () => {
    mockUseGetExperimentsQuery.mockReturnValue({
      data: undefined,
      isLoading: true,
    } as any)

    const result = useFeatureExperimentFreeze(42, 'env-123')

    expect(result.isFrozen).toBe(false)
    expect(result.isLoading).toBe(true)
  })

  it('skips query when featureId is undefined', () => {
    mockUseGetExperimentsQuery.mockReturnValue({
      data: undefined,
      isLoading: false,
    } as any)

    const result = useFeatureExperimentFreeze(undefined, 'env-123')

    expect(result.isFrozen).toBe(false)
    expect(mockUseGetExperimentsQuery).toHaveBeenCalledWith(
      expect.objectContaining({ environmentId: 'env-123' }),
      expect.objectContaining({ skip: true }),
    )
  })
})
