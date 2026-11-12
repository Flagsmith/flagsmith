import { getChangeRequestFeature } from 'common/utils/getChangeRequestFeature'

describe('getChangeRequestFeature', () => {
  it('returns undefined before the change request loads', () => {
    expect(getChangeRequestFeature(undefined)).toBeUndefined()
  })

  it('reads the feature from the first feature state', () => {
    expect(
      getChangeRequestFeature({
        change_sets: [{ feature: 2 }],
        feature_states: [{ feature: 1 }],
      }),
    ).toBe(1)
  })

  it('falls back to the first change set', () => {
    expect(
      getChangeRequestFeature({
        change_sets: [{ feature: 2 }],
        feature_states: [],
      }),
    ).toBe(2)
  })

  it('returns undefined when neither names a feature', () => {
    expect(getChangeRequestFeature({ feature_states: [] })).toBeUndefined()
  })
})
