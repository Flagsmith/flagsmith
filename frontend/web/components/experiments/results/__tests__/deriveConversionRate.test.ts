import moment from 'moment'
import { buildConversionChartData } from 'components/experiments/results/deriveConversionRate'
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

describe('buildConversionChartData', () => {
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
      // Bucket absent from the exposures series: conversions with no new
      // enrollments that day.
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
      buildConversionChartData(res, 7, identities, 'cumulative'),
    ).toBeNull()
  })

  it('returns null when no metric matches the requested id', () => {
    expect(
      buildConversionChartData(results, 999, identities, 'daily'),
    ).toBeNull()
  })

  it('accumulates running totals over the bucket union in cumulative mode', () => {
    const chart = buildConversionChartData(results, 7, identities, 'cumulative')
    expect(chart?.points).toEqual([
      { control: 60, day: '1 Jun', variant_a: 100 },
      { control: 90, day: '2 Jun', variant_a: 100 },
      // Carried forward across a bucket with exposures but no conversions.
      { control: 90, day: '3 Jun', variant_a: 100 },
    ])
    expect(chart?.seriesLabels.control).toBe('Control converted')
  })

  it('plots raw per-bucket increments in daily mode', () => {
    const chart = buildConversionChartData(results, 7, identities, 'daily')
    expect(chart?.points).toEqual([
      { control: 60, day: '1 Jun', variant_a: 100 },
      { control: 30, day: '2 Jun', variant_a: 0 },
      { control: 0, day: '3 Jun', variant_a: 0 },
    ])
    expect(chart?.seriesLabels.control).toBe('Control conversions')
  })

  it('adds the year to labels when the series spans calendar years', () => {
    const res = summary({
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
      metrics: [metricResult({ conversions_timeseries: conversions })],
    })
    const chart = buildConversionChartData(res, 7, identities, 'cumulative')
    expect(chart?.points.map((p) => p.day)).toEqual([
      '1 Jun 2026',
      '2 Jun 2026',
      '1 Jun 2027',
    ])
  })

  it('renders the last 30 day buckets, still accumulating from the start', () => {
    const days = Array.from({ length: 40 }, (_, i) =>
      moment.utc('2026-06-01').add(i, 'days').toISOString(true),
    )
    const res = summary({
      exposures_timeseries: exposuresTs(
        days.map((bucket) => ({ bucket, new_identities: { control: 10 } })),
      ),
      metrics: [
        metricResult({
          conversions_timeseries: conversionsTs(
            days.map((bucket) => ({
              bucket,
              converted_identities: { control: 1 },
            })),
          ),
        }),
      ],
    })
    const chart = buildConversionChartData(res, 7, identities, 'cumulative')
    expect(chart?.points).toHaveLength(30)
    // The window opens on day 11, carrying the 11 conversions to date.
    expect(chart?.points[0]).toEqual({
      control: 11,
      day: '11 Jun',
      variant_a: 0,
    })
  })
})
