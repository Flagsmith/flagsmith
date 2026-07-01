import {
  buildRolloutSummary,
  getControlPercentage,
  getEvenSplit,
  getRolloutSummaryRows,
  getTrafficSegments,
  getVariationSplitDefaults,
  toRolloutFeatureValue,
} from 'components/experiments/rollout'
import { MultivariateOption, ProjectFlag } from 'common/types/responses'

const option = (over: Partial<MultivariateOption>): MultivariateOption => ({
  boolean_value: undefined,
  default_percentage_allocation: 0,
  id: 1,
  integer_value: undefined,
  key: null,
  string_value: '',
  type: 'unicode',
  uuid: 'u',
  ...over,
})

const feature = (options: MultivariateOption[]): ProjectFlag =>
  ({ multivariate_options: options } as ProjectFlag)

describe('rollout helpers', () => {
  it('getEvenSplit splits weight evenly across control and variants', () => {
    expect(getEvenSplit([option({ id: 10 }), option({ id: 11 })])).toEqual([
      { multivariate_feature_option: 10, percentage_allocation: 33 },
      { multivariate_feature_option: 11, percentage_allocation: 33 },
    ])
  })

  it('getVariationSplitDefaults derives weights from the environment, falling back to feature defaults', () => {
    expect(
      getVariationSplitDefaults(
        [
          option({ default_percentage_allocation: 60, id: 10 }),
          option({ default_percentage_allocation: 40, id: 11 }),
        ],
        [{ multivariate_feature_option: 10, percentage_allocation: 70 }],
      ),
    ).toEqual([
      { multivariate_feature_option: 10, percentage_allocation: 70 },
      { multivariate_feature_option: 11, percentage_allocation: 40 },
    ])
  })

  it('getControlPercentage is 100 minus the sum of the split', () => {
    expect(
      getControlPercentage([
        { multivariate_feature_option: 10, percentage_allocation: 30 },
      ]),
    ).toBe(70)
  })

  it('getRolloutSummaryRows puts Control first, then variants by key/fallback', () => {
    expect(
      getRolloutSummaryRows(
        feature([
          option({ id: 10, key: 'big', string_value: 'big' }),
          option({ id: 11, key: null, string_value: 'small' }),
        ]),
        [
          { multivariate_feature_option: 10, percentage_allocation: 60 },
          { multivariate_feature_option: 11, percentage_allocation: 40 },
        ],
      ),
    ).toEqual([
      { label: 'Control', percentage: 0 },
      { label: 'big', percentage: 60 },
      { label: 'Variant_2', percentage: 40 },
    ])
  })

  it('getTrafficSegments scales each arm by the rollout percentage', () => {
    expect(
      getTrafficSegments(
        feature([option({ id: 10 }), option({ id: 11 })]),
        [
          { multivariate_feature_option: 10, percentage_allocation: 40 },
          { multivariate_feature_option: 11, percentage_allocation: 30 },
        ],
        50,
      ).map(({ label, percentage }) => ({ label, percentage })),
    ).toEqual([
      { label: 'Control', percentage: 15 },
      { label: 'Variant_1', percentage: 20 },
      { label: 'Variant_2', percentage: 15 },
    ])
  })

  it('toRolloutFeatureValue wraps a typed control value as { type, value }', () => {
    expect(toRolloutFeatureValue('control')).toEqual({
      type: 'string',
      value: 'control',
    })
    expect(toRolloutFeatureValue(42)).toEqual({ type: 'integer', value: '42' })
    expect(toRolloutFeatureValue(true)).toEqual({
      type: 'boolean',
      value: 'true',
    })
    expect(toRolloutFeatureValue(null)).toEqual({ type: 'string', value: '' })
  })

  it('buildRolloutSummary describes rollout and split in one sentence', () => {
    expect(
      buildRolloutSummary(42, [
        { label: 'Control', percentage: 0 },
        { label: 'big', percentage: 60 },
        { label: 'small', percentage: 40 },
      ]),
    ).toBe(
      '42% of eligible identities enter the experiment. Split: Control 0%, big 60%, small 40%.',
    )
  })
})
