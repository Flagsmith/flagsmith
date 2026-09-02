import { featureStateToValue } from 'common/utils/featureStateToValue'
import type { FlagsmithValue, TraitValue } from 'common/types/responses'

describe('featureStateToValue', () => {
  it.each([
    ['unicode', { string_value: '{"a":1}', type: 'unicode' }, '{"a":1}'],
    ['bool', { boolean_value: true, type: 'bool' }, true],
    ['float', { float_value: 1.5, type: 'float' }, 1.5],
    ['int', { integer_value: 7, type: 'int' }, 7],
  ])('flattens a nested %s value', (_label, nested, expected) => {
    expect(featureStateToValue(nested as never)).toBe(expected)
  })

  // Typed rather than cast, so these fail to compile if TraitValue drifts.
  it.each<[string, TraitValue, FlagsmithValue]>([
    [
      'int',
      {
        boolean_value: null,
        integer_value: 3,
        string_value: null,
        value_type: 'int',
      },
      3,
    ],
    [
      'float',
      {
        boolean_value: null,
        float_value: 2.5,
        integer_value: null,
        string_value: null,
        value_type: 'float',
      },
      2.5,
    ],
    [
      'bool',
      {
        boolean_value: false,
        integer_value: null,
        string_value: null,
        value_type: 'bool',
      },
      false,
    ],
    [
      'unicode',
      {
        boolean_value: null,
        integer_value: null,
        string_value: 'power_users',
        value_type: 'unicode',
      },
      'power_users',
    ],
  ])('reads value_type on a core trait (%s)', (_label, trait, expected) => {
    expect(featureStateToValue(trait)).toBe(expected)
  })

  it('normalises a missing int/float to null', () => {
    expect(featureStateToValue({ type: 'int' } as never)).toBeNull()
    expect(featureStateToValue({ type: 'float' } as never)).toBeNull()
  })

  it('returns null for null or undefined', () => {
    expect(featureStateToValue(null)).toBeNull()
    expect(featureStateToValue(undefined)).toBeNull()
  })

  it.each([
    ['string', 'already-flat'],
    ['number', 42],
    ['boolean false', false],
    ['empty string', ''],
  ])('passes an already-flat %s through unchanged', (_label, flat) => {
    expect(featureStateToValue(flat)).toBe(flat)
  })
})
