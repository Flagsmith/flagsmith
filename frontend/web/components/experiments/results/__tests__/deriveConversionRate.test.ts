import {
  REST_SUFFIX,
  buildConversionRateChartData,
  buildConversionStackChartData,
} from 'components/experiments/results/deriveConversionRate'
import type { ConversionStackChartData } from 'components/experiments/results/deriveConversionRate'
import type { VariantIdentity } from 'components/experiments/results/derive'
import {
  BayesianMetricResult,
  BayesianResultsSummary,
  ConversionsTimeseries,
  ExposuresTimeseries,
} from 'common/types/responses'

const identities: VariantIdentity[] = [
  {
    colour: '#111111',
    isControl: true,
    key: 'control',
    name: 'Control',
    value: 'off',
  },
  {
    colour: '#222222',
    isControl: false,
    key: 'variant_a',
    name: 'variant_a',
    value: 'on',
  },
]

const summary = (
  over: Partial<BayesianResultsSummary> = {},
): BayesianResultsSummary => ({
  metrics: [],
  srm_p_value: null,
  ...over,
})

const exposuresTs = (
  points: ExposuresTimeseries['points'],
): ExposuresTimeseries => ({ granularity: 'day', points })

const metricResult = (
  over: Partial<BayesianMetricResult> = {},
): BayesianMetricResult => ({
  conversions_timeseries: null,
  inference: {},
  metric_id: 7,
  variants: {},
  ...over,
})

const conversionsTs = (
  points: ConversionsTimeseries['points'],
): ConversionsTimeseries => ({ granularity: 'day', points })

describe('buildConversionRateChartData', () => {
  const exposures = exposuresTs([
    {
      bucket: '2026-06-01T00:00:00+00:00',
      new_identities: { control: 600, variant_a: 1000 },
    },
    {
      bucket: '2026-06-03T00:00:00+00:00',
      new_identities: { control: 400 },
    },
  ])

  it('returns null when exposures_timeseries is absent', () => {
    const results = summary({
      metrics: [metricResult({ conversions_timeseries: conversionsTs([]) })],
    })
    expect(buildConversionRateChartData(results, 7, identities)).toBeNull()
  })

  it('returns null when the metric has a null conversions_timeseries', () => {
    const results = summary({
      exposures_timeseries: exposures,
      metrics: [metricResult()],
    })
    expect(buildConversionRateChartData(results, 7, identities)).toBeNull()
  })

  it('returns null when no metric matches the requested id', () => {
    const results = summary({
      exposures_timeseries: exposures,
      metrics: [
        metricResult({
          conversions_timeseries: conversionsTs([
            {
              bucket: '2026-06-01T00:00:00+00:00',
              converted_identities: { control: 60 },
            },
          ]),
        }),
      ],
    })
    expect(buildConversionRateChartData(results, 999, identities)).toBeNull()
  })

  it('divides running conversions by running exposures over the bucket union', () => {
    const results = summary({
      exposures_timeseries: exposures,
      metrics: [
        metricResult({
          conversions_timeseries: conversionsTs([
            {
              bucket: '2026-06-01T00:00:00+00:00',
              converted_identities: { control: 60, variant_a: 100 },
            },
            {
              // Bucket absent from the exposures series: conversions with no
              // new enrollments that day.
              bucket: '2026-06-02T00:00:00+00:00',
              converted_identities: { control: 30 },
            },
          ]),
        }),
      ],
    })
    const chart = buildConversionRateChartData(results, 7, identities)
    expect(chart?.points).toEqual([
      // 60/600, 100/1000
      { control: 10, day: '1 Jun', variant_a: 10 },
      // 90/600, 100/1000 — exposures carried forward
      { control: 15, day: '2 Jun', variant_a: 10 },
      // 90/1000, 100/1000 — conversions carried forward
      { control: 9, day: '3 Jun', variant_a: 10 },
    ])
    expect(chart?.countsByDay['2 Jun']).toEqual({
      control: { converted: 90, exposed: 600 },
      variant_a: { converted: 100, exposed: 1000 },
    })
  })

  it('omits a variant from points until it has exposures', () => {
    const results = summary({
      exposures_timeseries: exposuresTs([
        {
          bucket: '2026-06-01T00:00:00+00:00',
          new_identities: { control: 600 },
        },
      ]),
      metrics: [
        metricResult({
          conversions_timeseries: conversionsTs([
            {
              bucket: '2026-06-01T00:00:00+00:00',
              converted_identities: { control: 60 },
            },
          ]),
        }),
      ],
    })
    const chart = buildConversionRateChartData(results, 7, identities)
    expect(chart?.points).toEqual([{ control: 10, day: '1 Jun' }])
  })

  it('adds the year to labels when the series spans calendar years', () => {
    const results = summary({
      exposures_timeseries: exposuresTs([
        {
          bucket: '2026-06-01T00:00:00+00:00',
          new_identities: { control: 600 },
        },
        {
          bucket: '2027-06-01T00:00:00+00:00',
          new_identities: { control: 400 },
        },
      ]),
      metrics: [
        metricResult({
          conversions_timeseries: conversionsTs([
            {
              bucket: '2026-06-01T00:00:00+00:00',
              converted_identities: { control: 60 },
            },
          ]),
        }),
      ],
    })
    const chart = buildConversionRateChartData(results, 7, identities)
    expect(chart?.points.map((p) => p.day)).toEqual([
      '1 Jun 2026',
      '1 Jun 2027',
    ])
    expect(chart?.countsByDay['1 Jun 2026'].control).toEqual({
      converted: 60,
      exposed: 600,
    })
    expect(chart?.countsByDay['1 Jun 2027'].control).toEqual({
      converted: 60,
      exposed: 1000,
    })
  })

  it('yields flat 0% lines for an empty conversions series', () => {
    const results = summary({
      exposures_timeseries: exposures,
      metrics: [metricResult({ conversions_timeseries: conversionsTs([]) })],
    })
    const chart = buildConversionRateChartData(results, 7, identities)
    expect(chart?.points.map((p) => p.control)).toEqual([0, 0])
  })
})

const seriesFor = (chart: ConversionStackChartData | null, key: string) =>
  chart?.series.find((s) => s.key === key)

describe('buildConversionStackChartData', () => {
  const exposures = exposuresTs([
    {
      bucket: '2026-06-01T00:00:00+00:00',
      new_identities: { control: 600, variant_a: 1000 },
    },
    {
      bucket: '2026-06-03T00:00:00+00:00',
      new_identities: { control: 400 },
    },
  ])
  const conversions = conversionsTs([
    {
      bucket: '2026-06-01T00:00:00+00:00',
      converted_identities: { control: 60, variant_a: 100 },
    },
    {
      bucket: '2026-06-02T00:00:00+00:00',
      converted_identities: { control: 30 },
    },
  ])
  const results = summary({
    exposures_timeseries: exposures,
    metrics: [metricResult({ conversions_timeseries: conversions })],
  })

  it.each([
    ['exposures_timeseries is absent', summary({ metrics: [metricResult()] })],
    [
      'the metric has no conversions_timeseries',
      summary({ exposures_timeseries: exposures, metrics: [metricResult()] }),
    ],
  ])('returns null when %s', (_, res) => {
    expect(
      buildConversionStackChartData(res, 7, identities, 'cumulative'),
    ).toBeNull()
  })

  it('stacks cumulative conversions inside cumulative exposures', () => {
    const chart = buildConversionStackChartData(
      results,
      7,
      identities,
      'cumulative',
    )
    expect(chart?.points).toEqual([
      {
        control: 60,
        [`control${REST_SUFFIX}`]: 540,
        day: '1 Jun',
        variant_a: 100,
        [`variant_a${REST_SUFFIX}`]: 900,
      },
      {
        control: 90,
        [`control${REST_SUFFIX}`]: 510,
        day: '2 Jun',
        variant_a: 100,
        [`variant_a${REST_SUFFIX}`]: 900,
      },
      {
        control: 90,
        [`control${REST_SUFFIX}`]: 910,
        day: '3 Jun',
        variant_a: 100,
        [`variant_a${REST_SUFFIX}`]: 900,
      },
    ])
    // Segments stack per variant; the remainder fades the variant colour.
    expect(seriesFor(chart, 'control')?.stackId).toBe('control')
    expect(seriesFor(chart, `control${REST_SUFFIX}`)).toEqual({
      colour: '#111111',
      key: `control${REST_SUFFIX}`,
      label: 'Control exposures',
      opacity: 0.25,
      stackId: 'control',
    })
  })

  it('plots raw per-bucket increments side by side in daily mode', () => {
    const chart = buildConversionStackChartData(results, 7, identities, 'daily')
    expect(chart?.points).toEqual([
      {
        control: 60,
        [`control${REST_SUFFIX}`]: 600,
        day: '1 Jun',
        variant_a: 100,
        [`variant_a${REST_SUFFIX}`]: 1000,
      },
      {
        control: 30,
        [`control${REST_SUFFIX}`]: 0,
        day: '2 Jun',
        variant_a: 0,
        [`variant_a${REST_SUFFIX}`]: 0,
      },
      {
        control: 0,
        [`control${REST_SUFFIX}`]: 400,
        day: '3 Jun',
        variant_a: 0,
        [`variant_a${REST_SUFFIX}`]: 0,
      },
    ])
    // Daily quantities are not part-of-whole (a day's first conversions can
    // exceed its new exposures), so each series gets its own stack
    // (side-by-side bars) and the faded series becomes "new exposures".
    expect(seriesFor(chart, 'control')?.stackId).toBe('control')
    expect(seriesFor(chart, `control${REST_SUFFIX}`)).toEqual({
      colour: '#111111',
      key: `control${REST_SUFFIX}`,
      label: 'Control new exposures',
      opacity: 0.25,
      stackId: `control${REST_SUFFIX}`,
    })
  })
})
