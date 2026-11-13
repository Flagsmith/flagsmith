import {
  getFeatureValueLengthError,
  hasInvalidFeatureValueLength,
} from 'common/utils/featureValueValidation'

describe('getFeatureValueLengthError', () => {
  it('accepts values up to the configured maximum', () => {
    expect(getFeatureValueLengthError('x'.repeat(20_000))).toBeUndefined()
  })

  it('reports the actual and maximum character counts when exceeded', () => {
    expect(getFeatureValueLengthError('x'.repeat(20_001))).toBe(
      'Flag value is 20,001 characters. Maximum length is 20,000 characters.',
    )
  })

  it('counts Unicode code points as characters', () => {
    expect(getFeatureValueLengthError('😀'.repeat(20_001))).toContain(
      '20,001 characters',
    )
  })

  it('does not apply the string limit to non-string values', () => {
    expect(getFeatureValueLengthError(20_001)).toBeUndefined()
  })

  it('detects any over-limit value in a save', () => {
    expect(hasInvalidFeatureValueLength(['valid', 'x'.repeat(20_001)])).toBe(
      true,
    )
    expect(hasInvalidFeatureValueLength(['valid', 'also valid'])).toBe(false)
  })
})
