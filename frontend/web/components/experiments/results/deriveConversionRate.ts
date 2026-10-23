import moment from 'moment'
import { ChartDataPoint } from 'components/charts'
import {
  BayesianResultsSummary,
  ConversionsTimeseries,
  ExposuresTimeseries,
} from 'common/types/responses'
import {
  ExposuresChartData,
  VariantIdentity,
  formatBucketLabel,
  getMetricResult,
} from './derive'

type AccumulatedBucket = {
  day: string
  converted: Record<string, number>
}

// The backend returns every bucket since the experiment started, uncapped.
const MAX_DAY_BUCKETS = 30

// Walks the union of both series' buckets in time order, so a bucket carrying
// exposures but no conversions still appears, and carries the running
// conversion total forward across it.
const accumulateBuckets = (
  exposures: ExposuresTimeseries,
  identities: VariantIdentity[],
  conversions: ConversionsTimeseries,
): AccumulatedBucket[] => {
  const convertedByBucket: Record<string, Record<string, number>> = {}
  conversions.points.forEach((p) => {
    convertedByBucket[p.bucket] = p.converted_identities
  })

  // Sorting the ISO keys is chronological only because the warehouse emits a
  // uniform '+00:00' offset (the UTC invariant derive.ts documents for
  // labelling).
  const buckets = Array.from(
    new Set([
      ...exposures.points.map((p) => p.bucket),
      ...Object.keys(convertedByBucket),
    ]),
  ).sort()

  // Only the rendered window is trimmed: running totals still accumulate from
  // the experiment start.
  const from =
    exposures.granularity === 'day'
      ? Math.max(0, buckets.length - MAX_DAY_BUCKETS)
      : 0

  // Labels key the chart category, so they must be unique: a window spanning
  // calendar years adds the year to avoid '1 Jun' colliding with the same day
  // a year later.
  const spansYears =
    new Set(buckets.slice(from).map((bucket) => bucket.slice(0, 4))).size > 1
  const toLabel = (bucket: string) =>
    spansYears
      ? moment
          .utc(bucket)
          .format(
            exposures.granularity === 'hour'
              ? 'D MMM YYYY HH:mm'
              : 'D MMM YYYY',
          )
      : formatBucketLabel(bucket, exposures.granularity)

  const cumConverted: Record<string, number> = {}
  identities.forEach((v) => {
    cumConverted[v.key] = 0
  })

  const accumulated: AccumulatedBucket[] = []
  buckets.forEach((bucket, index) => {
    identities.forEach((v) => {
      cumConverted[v.key] += convertedByBucket[bucket]?.[v.key] ?? 0
    })
    if (index < from) return
    accumulated.push({
      converted: { ...cumConverted },
      day: toLabel(bucket),
    })
  })
  return accumulated
}

// Conversions per variant over time, as running totals.
export const buildConversionChartData = (
  results: BayesianResultsSummary,
  metricId: number,
  identities: VariantIdentity[],
): ExposuresChartData | null => {
  const exposures = results.exposures_timeseries
  const conversions = getMetricResult(results, metricId)?.conversions_timeseries
  if (!exposures || !conversions) return null

  const series: string[] = []
  const seriesLabels: Record<string, string> = {}
  const colorMap: Record<string, string> = {}
  identities.forEach((v) => {
    series.push(v.key)
    colorMap[v.key] = v.colour
    seriesLabels[v.key] = `${v.name} converted`
  })

  const points: ChartDataPoint[] = accumulateBuckets(
    exposures,
    identities,
    conversions,
  ).map((b) => {
    const point: ChartDataPoint = { day: b.day }
    identities.forEach((v) => {
      point[v.key] = b.converted[v.key]
    })
    return point
  })
  return { colorMap, points, series, seriesLabels }
}
