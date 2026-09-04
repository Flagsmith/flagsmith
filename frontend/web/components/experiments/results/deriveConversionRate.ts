import moment from 'moment'
import { BarSeries, ChartDataPoint } from 'components/charts'
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
  exposed: Record<string, number>
  converted: Record<string, number>
  // Raw per-bucket increments, for discrete (per-day) displays. Never divide
  // these — a bucket's first conversions can exceed its new exposures.
  newExposed: Record<string, number>
  newConverted: Record<string, number>
}

// Walks the union of both series' buckets in time order, carrying running
// totals forward across buckets missing from either series. Exposures bucket
// by first exposure and conversions by first conversion, so only these
// running totals may be divided (see ResultsSummary.exposures_timeseries in
// api/experimentation/dataclasses.py).
const accumulateBuckets = (
  exposures: ExposuresTimeseries,
  identities: VariantIdentity[],
  conversions?: ConversionsTimeseries | null,
): AccumulatedBucket[] => {
  const exposedByBucket: Record<string, Record<string, number>> = {}
  exposures.points.forEach((p) => {
    exposedByBucket[p.bucket] = p.new_identities
  })
  const convertedByBucket: Record<string, Record<string, number>> = {}
  conversions?.points.forEach((p) => {
    convertedByBucket[p.bucket] = p.converted_identities
  })

  // Sorting the ISO keys is chronological only because the warehouse emits a
  // uniform '+00:00' offset (the UTC invariant derive.ts documents for
  // labelling).
  const buckets = Array.from(
    new Set([
      ...Object.keys(exposedByBucket),
      ...Object.keys(convertedByBucket),
    ]),
  ).sort()

  // Labels key countsByDay and the chart category, so they must be unique:
  // a series spanning calendar years adds the year to avoid '1 Jun'
  // colliding with the same day a year later.
  const spansYears =
    new Set(buckets.map((bucket) => bucket.slice(0, 4))).size > 1
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

  const cumExposed: Record<string, number> = {}
  const cumConverted: Record<string, number> = {}
  identities.forEach((v) => {
    cumExposed[v.key] = 0
    cumConverted[v.key] = 0
  })

  return buckets.map((bucket) => {
    const newExposed: Record<string, number> = {}
    const newConverted: Record<string, number> = {}
    identities.forEach((v) => {
      newExposed[v.key] = exposedByBucket[bucket]?.[v.key] ?? 0
      newConverted[v.key] = convertedByBucket[bucket]?.[v.key] ?? 0
      cumExposed[v.key] += newExposed[v.key]
      cumConverted[v.key] += newConverted[v.key]
    })
    return {
      converted: { ...cumConverted },
      day: toLabel(bucket),
      exposed: { ...cumExposed },
      newConverted,
      newExposed,
    }
  })
}

// Rounded to one decimal for stable display.
const toRatePct = (converted: number, exposed: number): number =>
  Math.round((converted / exposed) * 1000) / 10

const seriesMeta = (identities: VariantIdentity[]) => {
  const seriesLabels: Record<string, string> = {}
  const colorMap: Record<string, string> = {}
  identities.forEach((v) => {
    seriesLabels[v.key] = v.name
    colorMap[v.key] = v.colour
  })
  return { colorMap, seriesLabels }
}

export type ConversionCounts = Record<
  string,
  { converted: number; exposed: number }
>

export type ConversionRateChartData = ExposuresChartData & {
  // Running numerator/denominator per bucket label, for tooltips.
  countsByDay: Record<string, ConversionCounts>
}

// Cumulative conversion rate per variant: running conversions over running
// exposures. A variant with no exposures yet is omitted from the point rather
// than shown as 0%.
export const buildConversionRateChartData = (
  results: BayesianResultsSummary,
  metricId: number,
  identities: VariantIdentity[],
): ConversionRateChartData | null => {
  const exposures = results.exposures_timeseries
  const conversions = getMetricResult(results, metricId)?.conversions_timeseries
  if (!exposures || !conversions) return null

  const series = identities.map((v) => v.key)
  const countsByDay: Record<string, ConversionCounts> = {}
  const points: ChartDataPoint[] = accumulateBuckets(
    exposures,
    identities,
    conversions,
  ).map((b) => {
    const point: ChartDataPoint = { day: b.day }
    const counts: ConversionCounts = {}
    identities.forEach((v) => {
      const exposed = b.exposed[v.key]
      if (exposed === 0) return
      point[v.key] = toRatePct(b.converted[v.key], exposed)
      counts[v.key] = { converted: b.converted[v.key], exposed }
    })
    countsByDay[b.day] = counts
    return point
  })
  return { countsByDay, points, series, ...seriesMeta(identities) }
}

export const REST_SUFFIX = '__rest'

export type ConversionStackMode = 'cumulative' | 'daily'

export type ConversionStackChartData = {
  points: ChartDataPoint[]
  series: BarSeries[]
}

// Stacked-bar encodings of exposures vs conversions per variant.
// 'cumulative': part-of-whole — the full bar is running exposures and the
// solid segment is running conversions (always a subset, since a first
// conversion can't precede a first exposure). 'daily': the raw per-bucket
// increments side by side — NOT part-of-whole, because a day's first
// conversions can exceed its new exposures, so no rate is implied.
export const buildConversionStackChartData = (
  results: BayesianResultsSummary,
  metricId: number,
  identities: VariantIdentity[],
  mode: ConversionStackMode,
): ConversionStackChartData | null => {
  const exposures = results.exposures_timeseries
  const conversions = getMetricResult(results, metricId)?.conversions_timeseries
  if (!exposures || !conversions) return null

  const daily = mode === 'daily'
  const series: BarSeries[] = identities.flatMap((v) => {
    const restKey = `${v.key}${REST_SUFFIX}`
    return [
      {
        colour: v.colour,
        key: v.key,
        label: daily ? `${v.name} conversions` : `${v.name} converted`,
        stackId: v.key,
      },
      {
        // The faded segment reuses the variant colour via fill-opacity
        // (palette colours are CSS var() strings, so no alpha channel can be
        // appended).
        colour: v.colour,
        key: restKey,
        label: daily ? `${v.name} new exposures` : `${v.name} exposures`,
        opacity: 0.25,
        // Cumulative segments are part-of-whole, so they share the variant's
        // stack. Daily ones are not (a day's first conversions can exceed its
        // new exposures), so they sit side by side.
        stackId: daily ? restKey : v.key,
      },
    ]
  })

  const points: ChartDataPoint[] = accumulateBuckets(
    exposures,
    identities,
    conversions,
  ).map((b) => {
    const point: ChartDataPoint = { day: b.day }
    identities.forEach((v) => {
      point[v.key] = daily ? b.newConverted[v.key] : b.converted[v.key]
      point[`${v.key}${REST_SUFFIX}`] = daily
        ? b.newExposed[v.key]
        : b.exposed[v.key] - b.converted[v.key]
    })
    return point
  })
  return { points, series }
}
