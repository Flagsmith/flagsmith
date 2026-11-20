import {
  formatFeatureValueLengthErrors,
  getFeatureSaveLengthErrors,
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
    expect(getFeatureValueLengthError('😀'.repeat(20_000))).toBeUndefined()
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

describe('getFeatureSaveLengthErrors', () => {
  const oversized = 'x'.repeat(20_001)

  it('collects errors across flag, variant, and active segment override values', () => {
    const errors = getFeatureSaveLengthErrors({
      flagValue: oversized,
      multivariateOptions: [
        { key: 'variant_a', string_value: oversized },
        { key: 'variant_b', string_value: 'ok' },
      ],
      segmentOverrides: [
        { segment_name: 'beta', value: oversized },
        { segment_name: 'stable', value: 'ok' },
      ],
    })

    expect(errors).toHaveLength(3)
    expect(errors[0]).toContain('Flag value')
    expect(errors[1]).toContain('Variant variant_a value')
    expect(errors[2]).toContain('Segment override beta value')
  })

  it('labels identity override errors', () => {
    const errors = getFeatureSaveLengthErrors({
      flagValue: oversized,
      isIdentity: true,
    })

    expect(errors).toHaveLength(1)
    expect(errors[0]).toContain('Identity override')
  })

  it('ignores oversized segment overrides marked for removal', () => {
    const errors = getFeatureSaveLengthErrors({
      flagValue: 'ok',
      segmentOverrides: [
        { segment_name: 'removing', toRemove: true, value: oversized },
      ],
    })

    expect(errors).toEqual([])
  })
})

describe('formatFeatureValueLengthErrors', () => {
  it('returns a single error unchanged and summarises multiple errors in one message', () => {
    expect(formatFeatureValueLengthErrors([])).toBe('')
    expect(formatFeatureValueLengthErrors(['Flag value is too long.'])).toBe(
      'Flag value is too long.',
    )
    expect(
      formatFeatureValueLengthErrors([
        'Flag value is too long.',
        'Variant 1 value is too long.',
      ]),
    ).toBe(
      '2 values exceed the maximum length: Flag value is too long. Variant 1 value is too long.',
    )
  })
})
