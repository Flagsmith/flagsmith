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

  it('returns the state matching the feature id', () => {
    const results = [make(10, 1), make(11, 99), make(12, 2)]
    expect(pickEnvironmentFlag(results, 99)).toBe(results[1])
  })

  it('falls back to the first result when there is no exact match', () => {
    const results = [make(10, 1), make(12, 2)]
    expect(pickEnvironmentFlag(results, 99)).toBe(results[0])
  })

  it('returns undefined when there are no results', () => {
    expect(pickEnvironmentFlag([], 99)).toBeUndefined()
    expect(pickEnvironmentFlag(undefined, 99)).toBeUndefined()
  })
})
