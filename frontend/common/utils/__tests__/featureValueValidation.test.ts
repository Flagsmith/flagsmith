import {
  formatFeatureValueLengthErrors,
  getFeatureSaveLengthErrors,
  getFeatureValueLengthError,
  getMaxFeatureValueLength,
  hasInvalidFeatureValueLength,
  MAX_FEATURE_VALUE_LENGTH,
} from 'common/utils/featureValueValidation'

describe('getMaxFeatureValueLength', () => {
  let originalProject: unknown
  let originalOverrides: unknown

  beforeEach(() => {
    originalProject = Reflect.get(globalThis, 'Project')
    originalOverrides = Reflect.get(globalThis, 'projectOverrides')
  })

  afterEach(() => {
    Reflect.set(globalThis, 'Project', originalProject)
    Reflect.set(globalThis, 'projectOverrides', originalOverrides)
  })

  it('falls back to the default limit when no runtime override is configured', () => {
    // Given
    Reflect.set(globalThis, 'Project', undefined)
    Reflect.set(globalThis, 'projectOverrides', undefined)

    // When
    const limit = getMaxFeatureValueLength()

    // Then
    expect(limit).toBe(MAX_FEATURE_VALUE_LENGTH)
  })

  it('uses Project.featureValueLimit when configured at runtime', () => {
    // Given
    Reflect.set(globalThis, 'Project', { featureValueLimit: 50_000 })
    Reflect.set(globalThis, 'projectOverrides', undefined)

    // When
    const limit = getMaxFeatureValueLength()

    // Then
    expect(limit).toBe(50_000)
  })

  it('uses projectOverrides.featureValueLimit when Project does not define one', () => {
    // Given
    Reflect.set(globalThis, 'Project', {})
    Reflect.set(globalThis, 'projectOverrides', { featureValueLimit: '32000' })

    // When
    const limit = getMaxFeatureValueLength()

    // Then
    expect(limit).toBe(32_000)
  })
})

describe('getFeatureValueLengthError', () => {
  it('accepts values up to the configured maximum', () => {
    // Given
    const value = 'x'.repeat(20_000)

    // When
    const error = getFeatureValueLengthError(value)

    // Then
    expect(error).toBeUndefined()
  })

  it('reports the actual and maximum character counts when exceeded', () => {
    // Given
    const value = 'x'.repeat(20_001)

    // When
    const error = getFeatureValueLengthError(value)

    // Then
    expect(error).toBe(
      'Flag value is 20,001 characters. Maximum length is 20,000 characters.',
    )
  })

  it('counts Unicode code points as characters', () => {
    // Given
    const atLimit = '😀'.repeat(20_000)
    const overLimit = '😀'.repeat(20_001)

    // When
    const atLimitError = getFeatureValueLengthError(atLimit)
    const overLimitError = getFeatureValueLengthError(overLimit)

    // Then
    expect(atLimitError).toBeUndefined()
    expect(overLimitError).toContain('20,001 characters')
  })

  it('does not apply the string limit to non-string values', () => {
    // Given
    const numericValue = 20_001

    // When
    const error = getFeatureValueLengthError(numericValue)

    // Then
    expect(error).toBeUndefined()
  })

  it('detects any over-limit value in a save', () => {
    // Given
    const withOversized = ['valid', 'x'.repeat(20_001)]
    const allValid = ['valid', 'also valid']

    // When
    const hasInvalid = hasInvalidFeatureValueLength(withOversized)
    const hasValidOnly = hasInvalidFeatureValueLength(allValid)

    // Then
    expect(hasInvalid).toBe(true)
    expect(hasValidOnly).toBe(false)
  })

  it('respects an explicit custom maxLength', () => {
    // Given
    const value = 'x'.repeat(11)

    // When
    const error = getFeatureValueLengthError(value, 'Flag value', 10)
    const allowed = getFeatureValueLengthError(value, 'Flag value', 11)

    // Then
    expect(error).toBe(
      'Flag value is 11 characters. Maximum length is 10 characters.',
    )
    expect(allowed).toBeUndefined()
  })
})

describe('getFeatureSaveLengthErrors', () => {
  const oversized = 'x'.repeat(20_001)

  it('collects errors across flag, variant, and active segment override values', () => {
    // Given
    const payload = {
      flagValue: oversized,
      multivariateOptions: [
        { key: 'variant_a', string_value: oversized },
        { key: 'variant_b', string_value: 'ok' },
      ],
      segmentOverrides: [
        { segment_name: 'beta', value: oversized },
        { segment_name: 'stable', value: 'ok' },
      ],
    }

    // When
    const errors = getFeatureSaveLengthErrors(payload)

    // Then
    expect(errors).toHaveLength(3)
    expect(errors[0]).toContain('Flag value')
    expect(errors[1]).toContain('Variant variant_a value')
    expect(errors[2]).toContain('Segment override beta value')
  })

  it('labels identity override errors', () => {
    // Given
    const payload = {
      flagValue: oversized,
      isIdentity: true,
    }

    // When
    const errors = getFeatureSaveLengthErrors(payload)

    // Then
    expect(errors).toHaveLength(1)
    expect(errors[0]).toContain('Identity override')
  })

  it('ignores oversized segment overrides marked for removal', () => {
    // Given
    const payload = {
      flagValue: 'ok',
      segmentOverrides: [
        { segment_name: 'removing', toRemove: true, value: oversized },
      ],
    }

    // When
    const errors = getFeatureSaveLengthErrors(payload)

    // Then
    expect(errors).toEqual([])
  })

  it('validates all save fields against a custom maxLength', () => {
    // Given
    const payload = {
      flagValue: 'x'.repeat(25),
      maxLength: 20,
      multivariateOptions: [{ key: 'variant_a', string_value: 'y'.repeat(21) }],
    }

    // When
    const errors = getFeatureSaveLengthErrors(payload)

    // Then
    expect(errors).toHaveLength(2)
    expect(errors[0]).toContain('Maximum length is 20 characters.')
    expect(errors[1]).toContain('Variant variant_a value')
  })
})

describe('formatFeatureValueLengthErrors', () => {
  it('returns a single error unchanged and summarises multiple errors in one message', () => {
    // Given
    const empty: string[] = []
    const single = ['Flag value is too long.']
    const multiple = ['Flag value is too long.', 'Variant 1 value is too long.']

    // When
    const formattedEmpty = formatFeatureValueLengthErrors(empty)
    const formattedSingle = formatFeatureValueLengthErrors(single)
    const formattedMultiple = formatFeatureValueLengthErrors(multiple)

    // Then
    expect(formattedEmpty).toBe('')
    expect(formattedSingle).toBe('Flag value is too long.')
    expect(formattedMultiple).toBe(
      '2 values exceed the maximum length: Flag value is too long. Variant 1 value is too long.',
    )
  })
})
