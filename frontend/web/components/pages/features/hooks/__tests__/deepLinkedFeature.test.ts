// `pickEnvironmentFlag` pulls in `common/utils/utils`, whose stores reach for
// `window` globals (via the flux dispatcher) that aren't available under the
// jest `node` test environment, so they're mocked out here.
jest.mock('common/stores/account-store', () => ({}))
jest.mock('common/stores/project-store', () => ({}))
jest.mock('common/store', () => ({ getStore: () => ({}) }))
jest.mock('@flagsmith/flagsmith', () => ({
  getValue: (_key: string, opts: { fallback: unknown }) => opts.fallback,
}))

import {
  pickEnvironmentFlag,
  shouldDeepFetchFeature,
} from 'components/pages/features/hooks/deepLinkedFeature'
import type { FeatureState } from 'common/types/responses'

const projectFlags = [{ id: 1 }, { id: 2 }, { id: 3 }]

describe('shouldDeepFetchFeature', () => {
  it('returns null when there is no feature param', () => {
    expect(
      shouldDeepFetchFeature({
        featureParam: undefined,
        isListLoaded: true,
        projectFlags,
      }),
    ).toBeNull()
  })

  it('returns null when the list has not loaded yet', () => {
    expect(
      shouldDeepFetchFeature({
        featureParam: '99',
        isListLoaded: false,
        projectFlags: [],
      }),
    ).toBeNull()
  })

  it('returns null when the feature is on the current page', () => {
    expect(
      shouldDeepFetchFeature({
        featureParam: '2',
        isListLoaded: true,
        projectFlags,
      }),
    ).toBeNull()
  })

  it('returns the feature id when the feature is off the current page', () => {
    expect(
      shouldDeepFetchFeature({
        featureParam: '99',
        isListLoaded: true,
        projectFlags,
      }),
    ).toEqual({ featureId: 99 })
  })

  it('returns null for a non-numeric feature param', () => {
    expect(
      shouldDeepFetchFeature({
        featureParam: 'not-a-number',
        isListLoaded: true,
        projectFlags,
      }),
    ).toBeNull()
  })
})

describe('pickEnvironmentFlag', () => {
  const make = (id: number, feature: number) =>
    ({ feature, id } as FeatureState)

  // `features/featurestates/` returns feature_state_value as a nested object,
  // unlike the paginated feature list which flattens it to a scalar.
  const makeNested = (
    id: number,
    feature: number,
    featureStateValue: Record<string, unknown>,
  ) =>
    ({
      enabled: true,
      feature,
      feature_state_value: featureStateValue,
      id,
    } as unknown as FeatureState)

  it('returns the state matching the feature id', () => {
    const results = [make(10, 1), make(11, 99), make(12, 2)]
    expect(pickEnvironmentFlag(results, 99)).toEqual({
      ...results[1],
      feature_state_value: null,
    })
  })

  it('falls back to the first result when there is no exact match', () => {
    const results = [make(10, 1), make(12, 2)]
    expect(pickEnvironmentFlag(results, 99)).toEqual({
      ...results[0],
      feature_state_value: null,
    })
  })

  it('returns undefined when there are no results', () => {
    expect(pickEnvironmentFlag([], 99)).toBeUndefined()
    expect(pickEnvironmentFlag(undefined, 99)).toBeUndefined()
  })

  it('flattens a nested unicode feature state value', () => {
    const results = [
      makeNested(11, 99, {
        boolean_value: null,
        integer_value: null,
        string_value: 'real value',
        type: 'unicode',
      }),
    ]
    expect(pickEnvironmentFlag(results, 99)?.feature_state_value).toBe(
      'real value',
    )
  })

  it('flattens a nested int feature state value', () => {
    const results = [
      makeNested(11, 99, {
        boolean_value: null,
        integer_value: 42,
        string_value: null,
        type: 'int',
      }),
    ]
    expect(pickEnvironmentFlag(results, 99)?.feature_state_value).toBe(42)
  })

  it('flattens a nested bool feature state value of false', () => {
    const results = [
      makeNested(11, 99, {
        boolean_value: false,
        integer_value: null,
        string_value: null,
        type: 'bool',
      }),
    ]
    expect(pickEnvironmentFlag(results, 99)?.feature_state_value).toBe(false)
  })

  it('never returns an object that would render as [object Object]', () => {
    const results = [
      makeNested(11, 99, {
        boolean_value: null,
        integer_value: null,
        string_value: 'real value',
        type: 'unicode',
      }),
    ]
    const value = pickEnvironmentFlag(results, 99)?.feature_state_value
    expect(typeof value).not.toBe('object')
    expect(`${value}`).not.toBe('[object Object]')
  })

  it('preserves the other feature state fields while flattening', () => {
    const results = [
      makeNested(11, 99, {
        boolean_value: null,
        integer_value: null,
        string_value: 'real value',
        type: 'unicode',
      }),
    ]
    expect(pickEnvironmentFlag(results, 99)).toEqual({
      enabled: true,
      feature: 99,
      feature_state_value: 'real value',
      id: 11,
    })
  })
})
