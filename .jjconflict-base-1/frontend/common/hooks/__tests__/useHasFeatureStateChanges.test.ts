jest.mock('common/services/useFeatureState', () => ({
  getFeatureStates: jest.fn(),
  useGetFeatureStatesQuery: jest.fn(),
}))

jest.mock('common/services/useSegment', () => ({
  getSegments: jest.fn(),
  useGetSegmentsQuery: jest.fn(),
}))

// The hook imports getFeatureStateCrud from the feature version service, which
// drags in the store and browser-only modules; stub those and keep the crud
// logic real.
jest.mock('common/store', () => ({ getStore: jest.fn() }))

jest.mock('common/service', () => ({
  service: {
    enhanceEndpoints: () => ({ injectEndpoints: () => ({}) }),
  },
}))

jest.mock('common/services/useVersionFeatureState', () => ({
  getVersionFeatureState: jest.fn(),
}))

jest.mock('common/utils/utils', () => ({
  __esModule: true,
  default: {
    featureStateToValue: (value: unknown) => value,
    getTypedValue: (value: unknown) => value,
  },
}))

jest.mock('react', () => ({
  ...jest.requireActual('react'),
  useMemo: (fn: () => any) => fn(),
}))

import { useHasFeatureStateChanges } from 'common/hooks/useHasFeatureStateChanges'
import { useGetFeatureStatesQuery } from 'common/services/useFeatureState'
import { useGetSegmentsQuery } from 'common/services/useSegment'

const mockUseGetFeatureStatesQuery =
  useGetFeatureStatesQuery as jest.MockedFunction<
    typeof useGetFeatureStatesQuery
  >
const mockUseGetSegmentsQuery = useGetSegmentsQuery as jest.MockedFunction<
  typeof useGetSegmentsQuery
>

const FEATURE_ID = 10
const SEGMENT_ID = 7

// Feature state of the environment itself (no segment)
const environmentFeatureState = {
  enabled: true,
  feature: FEATURE_ID,
  feature_segment: null,
  feature_state_value: 'value',
  id: 100,
  multivariate_feature_state_values: [],
}

// Existing segment override, as stored on the server
const segmentOverrideFeatureState = {
  enabled: false,
  feature: FEATURE_ID,
  feature_segment: {
    environment: 1,
    id: 200,
    priority: 0,
    segment: SEGMENT_ID,
  },
  feature_state_value: 'override',
  id: 200,
  multivariate_feature_state_values: [],
}

const storedFeatureStates = [
  segmentOverrideFeatureState,
  environmentFeatureState,
]

const segments = [{ feature: FEATURE_ID, id: SEGMENT_ID, name: 'beta users' }]

describe('useHasFeatureStateChanges', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseGetFeatureStatesQuery.mockReturnValue({
      data: { results: storedFeatureStates },
    } as any)
    mockUseGetSegmentsQuery.mockReturnValue({
      data: { results: segments },
    } as any)
  })

  const params = { environmentId: 1, featureId: FEATURE_ID, projectId: 1 }

  it('returns false when nothing differs from the stored feature states', () => {
    const result = useHasFeatureStateChanges({
      ...params,
      featureStates: storedFeatureStates,
    })

    expect(result).toBe(false)
  })

  it('returns true when a segment override is marked for removal', () => {
    const featureStates = [
      { ...segmentOverrideFeatureState, toRemove: true },
      environmentFeatureState,
    ]

    const result = useHasFeatureStateChanges({ ...params, featureStates })

    expect(result).toBe(true)
  })

  it('returns true when the environment value changes', () => {
    const featureStates = [
      segmentOverrideFeatureState,
      { ...environmentFeatureState, feature_state_value: 'new value' },
    ]

    const result = useHasFeatureStateChanges({ ...params, featureStates })

    expect(result).toBe(true)
  })
})
