import { featureStateToValue } from 'common/utils/featureStateToValue'

describe('featureStateToValue', () => {
  it.each([
    ['unicode', { string_value: '{"a":1}', type: 'unicode' }, '{"a":1}'],
    ['bool', { boolean_value: true, type: 'bool' }, true],
    ['float', { float_value: 1.5, type: 'float' }, 1.5],
    ['int', { integer_value: 7, type: 'int' }, 7],
  ])('flattens a nested %s value', (_label, nested, expected) => {
    expect(featureStateToValue(nested as never)).toBe(expected)
  })

  it('reads value_type when present (core traits)', () => {
    expect(
      featureStateToValue({ integer_value: 3, value_type: 'int' } as never),
    ).toBe(3)
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
