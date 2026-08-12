import {
  getDefaultVariantKey,
  hasUnmatchedIdentityOverride,
  sortMultivariateOptions,
} from 'common/utils/multivariate'

describe('multivariate', () => {
  describe('getDefaultVariantKey', () => {
    it.each`
      index | expected
      ${0}  | ${'Variant_1'}
      ${1}  | ${'Variant_2'}
      ${9}  | ${'Variant_10'}
    `(
      'getDefaultVariantKey($index) returns $expected',
      ({ expected, index }) => {
        expect(getDefaultVariantKey(index)).toBe(expected)
      },
    )
  })

  describe('sortMultivariateOptions', () => {
    it('sorts options by id ascending', () => {
      const options = [{ id: 3 }, { id: 1 }, { id: 2 }]

      expect(sortMultivariateOptions(options)).toEqual([
        { id: 1 },
        { id: 2 },
        { id: 3 },
      ])
    })

    it('sorts unsaved options last, preserving their input order', () => {
      const options = [
        { id: undefined, value: 'new_a' },
        { id: 2, value: 'saved' },
        { id: null, value: 'new_b' },
      ]

      expect(sortMultivariateOptions(options)).toEqual([
        { id: 2, value: 'saved' },
        { id: undefined, value: 'new_a' },
        { id: null, value: 'new_b' },
      ])
    })

    it('does not mutate the input array', () => {
      const options = [{ id: 2 }, { id: 1 }]

      sortMultivariateOptions(options)

      expect(options).toEqual([{ id: 2 }, { id: 1 }])
    })
  })

  describe('hasUnmatchedIdentityOverride', () => {
    it('detects an override kept from before the flag became multivariate', () => {
      expect(
        hasUnmatchedIdentityOverride({
          controlValue: 'ENV_DEFAULT',
          overrideValue: 'MY_OVERRIDE',
          variationOverrides: [],
        }),
      ).toBe(true)
    })

    it('does not flag an identity sitting on the control value', () => {
      expect(
        hasUnmatchedIdentityOverride({
          controlValue: 'ENV_DEFAULT',
          overrideValue: 'ENV_DEFAULT',
          variationOverrides: [],
        }),
      ).toBe(false)
    })

    it('does not flag an identity assigned a variation', () => {
      expect(
        hasUnmatchedIdentityOverride({
          controlValue: 'ENV_DEFAULT',
          overrideValue: 'MY_OVERRIDE',
          variationOverrides: [{ percentage_allocation: 100 }],
        }),
      ).toBe(false)
    })

    it('flags a partially weighted override, which does not pin a variation', () => {
      expect(
        hasUnmatchedIdentityOverride({
          controlValue: 'ENV_DEFAULT',
          overrideValue: 'MY_OVERRIDE',
          variationOverrides: [{ percentage_allocation: 60 }],
        }),
      ).toBe(true)
    })

    it.each`
      controlValue | overrideValue | expected
      ${null}      | ${undefined}  | ${false}
      ${undefined} | ${null}       | ${false}
      ${null}      | ${''}         | ${true}
      ${''}        | ${null}       | ${true}
      ${0}         | ${false}      | ${true}
    `(
      'treats control $controlValue against override $overrideValue as $expected',
      ({ controlValue, expected, overrideValue }) => {
        expect(
          hasUnmatchedIdentityOverride({
            controlValue,
            overrideValue,
            variationOverrides: undefined,
          }),
        ).toBe(expected)
      },
    )
  })
})
