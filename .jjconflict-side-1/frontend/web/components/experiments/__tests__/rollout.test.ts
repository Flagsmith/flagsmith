import {
  AudienceSegment,
  buildAudienceDescription,
  buildRolloutBody,
  buildRolloutSummary,
  getControlPercentage,
  getEvenSplit,
  getRolloutSummaryRows,
  getTrafficSegments,
  getVariationSplitDefaults,
  toAudiencePayload,
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

  it('buildRolloutSummary names the audience when segments are targeted', () => {
    expect(
      buildRolloutSummary(100, [{ label: 'Control', percentage: 100 }], {
        match: 'any',
        segments: [{ name: 'Beta users' }],
      }),
    ).toBe(
      '100% of identities in Beta users enter the experiment. Split: Control 100%.',
    )
  })
})

describe('buildAudienceDescription', () => {
  const named = (...names: string[]) => names.map((name) => ({ name }))

  it.each([
    ['no audience', undefined, 'eligible identities'],
    [
      'an empty audience',
      { match: 'any' as const, segments: [] },
      'eligible identities',
    ],
    [
      'one segment',
      { match: 'any' as const, segments: named('Beta users') },
      'identities in Beta users',
    ],
    [
      'two segments matching any',
      { match: 'any' as const, segments: named('Beta users', 'EU cohort') },
      'identities in Beta users or EU cohort',
    ],
    [
      'two segments matching all',
      { match: 'all' as const, segments: named('Beta users', 'EU cohort') },
      'identities in Beta users and EU cohort',
    ],
    [
      'three segments matching any',
      { match: 'any' as const, segments: named('Beta', 'EU', 'Mobile') },
      'identities in Beta, EU or Mobile',
    ],
  ])('%s', (_, audience, expected) => {
    expect(buildAudienceDescription(audience)).toBe(expected)
  })
})

const segment = (id: number): AudienceSegment => ({ id, name: `S${id}` })

describe('toAudiencePayload', () => {
  it('omits the audience when nothing is selected', () => {
    expect(toAudiencePayload([], 'any')).toBeUndefined()
  })

  it('maps the selection to ids, keeping the chosen match', () => {
    expect(toAudiencePayload([segment(12), segment(34)], 'all')).toEqual({
      match: 'all',
      segment_ids: [12, 34],
    })
  })
})

describe('buildRolloutBody', () => {
  const base = {
    enabled: false,
    featureStateValue: { type: 'string' as const, value: 'control' },
    rolloutPercentage: 100,
    variationSplit: [
      { multivariate_feature_option: 10, percentage_allocation: 50 },
    ],
  }

  // A present `audience` key is read as a replacement, so an experiment with no
  // audience and the detail page's save must both leave it off entirely rather
  // than send null or an empty list.
  it.each([
    ['the detail-page save, which passes no audience', undefined],
    ['the wizard with nothing selected', toAudiencePayload([], 'any')],
  ])('omits the audience key for %s', (_, audience) => {
    expect('audience' in buildRolloutBody({ ...base, audience })).toBe(false)
  })

  it('carries the match and segment ids when the wizard has a selection', () => {
    expect(
      buildRolloutBody({
        ...base,
        audience: toAudiencePayload([segment(12)], 'all'),
      }),
    ).toEqual({
      audience: { match: 'all', segment_ids: [12] },
      enabled: false,
      feature_state_value: { type: 'string', value: 'control' },
      multivariate_feature_state_values: base.variationSplit,
      rollout_percentage: 100,
    })
  })
})
