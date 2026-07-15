import {
  CONTROL_VARIANT_KEY,
  buildTicks,
  computeLiftRange,
  computeAxisRange,
  buildExposuresChartData,
  formatBucketLabel,
  getHeadlineTotal,
  getVariantIdentities,
  getVariantTotals,
  liftToPercent,
  valueToPercent,
} from 'components/experiments/results/derive'
import {
  BayesianMetricResult,
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

const metricResult: BayesianMetricResult = {
  inference: {
    b: {
      chance_to_win: 0.75,
      ci_high: 0.24,
      ci_low: -0.12,
      lift: 0.08,
    },
    c: {
      chance_to_win: 0.25,
      ci_high: 0.08,
      ci_low: -0.06,
      lift: -0.02,
    },
  },
  metric_id: 1,
  variants: {},
}

describe('axis helpers', () => {
  it('pads the axis range around treatment credible intervals', () => {
    expect(computeAxisRange(identities, metricResult)).toEqual({
      max: 0.294,
      min: -0.174,
    })
  })

  it('uses the default balanced range when there is no inference data', () => {
    expect(computeAxisRange(identities)).toEqual({
      max: 0.13,
      min: -0.13,
    })
  })

  it('converts values to percentages within an axis range', () => {
    expect(valueToPercent(0, { max: 0.3, min: -0.3 })).toBe(50)
    expect(valueToPercent(0.15, { max: 0.3, min: -0.3 })).toBe(75)
  })

  it('builds readable ticks for compact percentage ranges', () => {
    expect(buildTicks({ max: 0.13, min: -0.13 })).toEqual([
      -0.1, -0.05, 0, 0.05, 0.1,
    ])
  })
})

describe('liftToPercent', () => {
  it('centres zero and clamps values outside the range', () => {
    expect(liftToPercent(0, 0.3)).toBe(50)
    expect(liftToPercent(0.15, 0.3)).toBe(75)
    expect(liftToPercent(-0.6, 0.3)).toBe(0)
    expect(liftToPercent(0.6, 0.3)).toBe(100)
  })
})

describe('computeLiftRange', () => {
  it('pads the largest treatment interval magnitude beyond the default range', () => {
    expect(
      computeLiftRange(identities, {
        ...metricResult,
        inference: {
          ...metricResult.inference,
          b: {
            chance_to_win: 0.75,
            ci_high: 0.5,
            ci_low: -0.12,
            lift: 0.08,
          },
        },
      }),
    ).toBeCloseTo(0.55)
  })

  it('keeps a stable default range when there is no inference data', () => {
    expect(computeLiftRange(identities)).toBe(0.33)
  })

  it('keeps the stable default range for compact intervals', () => {
    expect(computeLiftRange(identities, metricResult)).toBe(0.33)
  })
})
