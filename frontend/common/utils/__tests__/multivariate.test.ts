import {
  getDefaultVariantKey,
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
})
