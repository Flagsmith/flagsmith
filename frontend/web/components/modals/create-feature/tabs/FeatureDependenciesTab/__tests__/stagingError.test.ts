import {
  describeApiError,
  toStagingError,
} from 'components/modals/create-feature/tabs/FeatureDependenciesTab/stagingError'

describe('describeApiError', () => {
  it.each([
    [{ data: { code: 'x', message: 'Refused.' } }, 'Refused.'],
    [{ data: { detail: 'Not found.' } }, 'Not found.'],
    [
      { data: { feature_states: ['This field is required.'] } },
      'feature_states: This field is required.',
    ],
    [{ status: 500 }, undefined],
    [undefined, undefined],
  ])('%j reads as %j', (error, expected) => {
    expect(describeApiError(error)).toBe(expected)
  })
})

describe('toStagingError', () => {
  it('keeps a staging error, with the row it refers to', () => {
    const error = { message: 'Refused.', prerequisiteId: 3 }
    expect(toStagingError(error, 'Fallback')).toBe(error)
  })

  it('reads an API error', () => {
    expect(toStagingError({ data: { detail: 'Nope.' } }, 'Fallback')).toEqual({
      message: 'Nope.',
    })
  })

  it('falls back when there is nothing to read', () => {
    expect(toStagingError({ status: 500 }, 'Fallback')).toEqual({
      message: 'Fallback',
    })
  })
})
