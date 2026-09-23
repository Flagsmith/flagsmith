import { sanitizeFeatureName } from 'common/utils/sanitizeFeatureName'

describe('sanitizeFeatureName', () => {
  it.each`
    raw                   | caseSensitive | expected
    ${'my flag'}          | ${false}      | ${'my_flag'}
    ${'My Flag'}          | ${false}      | ${'My_Flag'}
    ${'My Flag'}          | ${true}       | ${'my_flag'}
    ${'show demo button'} | ${true}       | ${'show_demo_button'}
    ${'already_ok'}       | ${false}      | ${'already_ok'}
    ${'UPPER'}            | ${true}       | ${'upper'}
    ${'UPPER'}            | ${false}      | ${'UPPER'}
    ${'a  b'}             | ${false}      | ${'a__b'}
    ${''}                 | ${false}      | ${''}
  `(
    'sanitizeFeatureName($raw, $caseSensitive) returns $expected',
    ({ caseSensitive, expected, raw }) => {
      expect(sanitizeFeatureName(raw, caseSensitive)).toBe(expected)
    },
  )
})
