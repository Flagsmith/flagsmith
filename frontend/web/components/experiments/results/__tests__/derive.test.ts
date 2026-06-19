import {
  CONTROL_VARIANT_KEY,
  buildExposuresChartData,
  formatBucketLabel,
  getHeadlineTotal,
  getVariantIdentities,
  getVariantTotals,
} from 'components/experiments/results/derive'
import {
  ExperimentFeature,
  ExposuresSummary,
  MultivariateOption,
} from 'common/types/responses'

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

const feature = (over: Partial<ExperimentFeature> = {}): ExperimentFeature => ({
  id: 1,
  initial_value: 'off',
  multivariate_options: [],
  name: 'checkout',
  type: 'MULTIVARIATE',
  ...over,
})

describe('getVariantIdentities', () => {
  it('puts control first using the feature initial value', () => {
    const result = getVariantIdentities(feature())
    expect(result[0]).toMatchObject({
      isControl: true,
      key: CONTROL_VARIANT_KEY,
      name: 'Control',
      value: 'off',
    })
  })

  it('names treatments by position and joins on the option key slug', () => {
    const result = getVariantIdentities(
      feature({
        multivariate_options: [
          option({
            id: 10,
            key: 'variant_b',
            string_value: 'big',
            type: 'unicode',
          }),
          option({
            id: 11,
            key: 'variant_c',
            string_value: 'huge',
            type: 'unicode',
          }),
        ],
      }),
    )
    expect(result.map((v) => [v.key, v.name, v.value, v.isControl])).toEqual([
      ['control', 'Control', 'off', true],
      ['variant_b', 'variant_b', 'big', false],
      ['variant_c', 'variant_c', 'huge', false],
    ])
  })

  it('assigns each variant a distinct colour', () => {
    const result = getVariantIdentities(
      feature({
        multivariate_options: [
          option({ id: 10, key: 'b' }),
          option({ id: 11, key: 'c' }),
        ],
      }),
    )
    const colours = result.map((v) => v.colour)
    expect(new Set(colours).size).toBe(colours.length)
  })

  it('falls back to a synthetic key and typed value when key is null', () => {
    const result = getVariantIdentities(
      feature({
        multivariate_options: [
          option({ id: 10, integer_value: 42, key: null, type: 'int' }),
        ],
      }),
    )
    expect(result[1]).toMatchObject({
      key: 'Variant_1',
      name: 'Variant_1',
      value: '42',
    })
  })
})

const identities = getVariantIdentities(
  feature({
    multivariate_options: [
      option({ id: 10, key: 'b', string_value: 'big' }),
      option({ id: 11, key: 'c', string_value: 'huge' }),
    ],
  }),
)

const summary: ExposuresSummary = {
  excluded_identities: 5,
  timeseries: {
    granularity: 'day',
    points: [
      {
        bucket: '2026-06-12T00:00:00+00:00',
        new_identities: { b: 10, control: 20 },
      },
      {
        bucket: '2026-06-13T00:00:00+00:00',
        new_identities: { c: 4, control: 5 },
      },
    ],
  },
}

describe('buildExposuresChartData', () => {
  it('produces cumulative series carrying forward missing variants', () => {
    const { points, series } = buildExposuresChartData(summary, identities)
    expect(series).toEqual(['control', 'b', 'c'])
    expect(points).toEqual([
      { b: 10, c: 0, control: 20, day: '12 Jun' },
      { b: 10, c: 4, control: 25, day: '13 Jun' },
    ])
  })

  it('maps colours and labels from identities', () => {
    const { colorMap, seriesLabels } = buildExposuresChartData(
      summary,
      identities,
    )
    expect(seriesLabels).toEqual({
      b: 'b',
      c: 'c',
      control: 'Control',
    })
    expect(Object.keys(colorMap).sort()).toEqual(['b', 'c', 'control'])
  })
})

describe('getVariantTotals / getHeadlineTotal', () => {
  it('totals each variant and computes share of the headline', () => {
    const headline = getHeadlineTotal(summary)
    expect(headline).toBe(39) // 20+10 + 5+4
    const totals = getVariantTotals(summary, identities)
    expect(totals.map((t) => [t.key, t.total])).toEqual([
      ['control', 25],
      ['b', 10],
      ['c', 4],
    ])
    expect(totals[0].share).toBeCloseTo(25 / 39)
  })

  it('returns zero shares when there is no data', () => {
    const empty: ExposuresSummary = {
      excluded_identities: 0,
      timeseries: { granularity: 'day', points: [] },
    }
    expect(getHeadlineTotal(empty)).toBe(0)
    expect(
      getVariantTotals(empty, identities).every((t) => t.share === 0),
    ).toBe(true)
  })
})

describe('formatBucketLabel', () => {
  it('formats day buckets as "D MMM"', () => {
    expect(formatBucketLabel('2026-06-12T00:00:00+00:00', 'day')).toBe('12 Jun')
  })
  it('formats hour buckets with the hour', () => {
    expect(formatBucketLabel('2026-06-12T14:00:00+00:00', 'hour')).toBe(
      '12 Jun 14:00',
    )
  })
})
