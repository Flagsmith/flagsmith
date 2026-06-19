import moment from 'moment'
import { ChartDataPoint, buildChartColorMap } from 'components/charts'
import {
  ExperimentFeature,
  ExposureGranularity,
  ExposuresSummary,
  MultivariateOption,
} from 'common/types/responses'

// Mirrors api/features/constants.py CONTROL_VARIANT_KEY.
export const CONTROL_VARIANT_KEY = 'control'

export type VariantIdentity = {
  key: string
  name: string
  value: string
  colour: string
  isControl: boolean
}

const getVariationValue = (mv: MultivariateOption): string => {
  if (mv.type === 'int') return String(mv.integer_value ?? '')
  if (mv.type === 'bool') return String(mv.boolean_value ?? '')
  return mv.string_value
}

export const getVariantIdentities = (
  feature: ExperimentFeature,
): VariantIdentity[] => {
  const options = feature.multivariate_options ?? []
  const keys = [
    CONTROL_VARIANT_KEY,
    ...options.map((mv, i) => mv.key ?? `Variant_${i + 1}`),
  ]
  const colourMap = buildChartColorMap(keys)
  const control: VariantIdentity = {
    colour: colourMap[CONTROL_VARIANT_KEY],
    isControl: true,
    key: CONTROL_VARIANT_KEY,
    name: 'Control',
    value: feature.initial_value ?? '',
  }
  const treatments: VariantIdentity[] = options.map((mv, i) => {
    const key = mv.key ?? `Variant_${i + 1}`
    return {
      colour: colourMap[key],
      isControl: false,
      key,
      name: key,
      value: getVariationValue(mv),
    }
  })
  return [control, ...treatments]
}

// Exposure buckets are computed in UTC by the warehouse query
// (toStartOfHour/Day(..., 'UTC')); render them in UTC so labels match.
export const formatBucketLabel = (
  isoBucket: string,
  granularity: ExposureGranularity,
): string =>
  moment.utc(isoBucket).format(granularity === 'hour' ? 'D MMM HH:mm' : 'D MMM')

export type ExposuresChartData = {
  points: ChartDataPoint[]
  series: string[]
  seriesLabels: Record<string, string>
  colorMap: Record<string, string>
}

export const buildExposuresChartData = (
  summary: ExposuresSummary,
  identities: VariantIdentity[],
): ExposuresChartData => {
  const series = identities.map((v) => v.key)
  const seriesLabels: Record<string, string> = {}
  const colorMap: Record<string, string> = {}
  identities.forEach((v) => {
    seriesLabels[v.key] = v.name
    colorMap[v.key] = v.colour
  })

  const running: Record<string, number> = {}
  series.forEach((key) => (running[key] = 0))

  const points: ChartDataPoint[] = summary.timeseries.points.map((point) => {
    series.forEach((key) => {
      running[key] += point.new_identities[key] ?? 0
    })
    return {
      day: formatBucketLabel(point.bucket, summary.timeseries.granularity),
      ...series.reduce<Record<string, number>>((acc, key) => {
        acc[key] = running[key]
        return acc
      }, {}),
    }
  })

  return { colorMap, points, series, seriesLabels }
}

export const getHeadlineTotal = (summary: ExposuresSummary): number =>
  summary.timeseries.points.reduce(
    (sum, point) =>
      sum + Object.values(point.new_identities).reduce((a, b) => a + b, 0),
    0,
  )

export type VariantTotal = {
  key: string
  name: string
  colour: string
  total: number
  share: number
}

export const getVariantTotals = (
  summary: ExposuresSummary,
  identities: VariantIdentity[],
): VariantTotal[] => {
  const headline = getHeadlineTotal(summary)
  return identities.map((v) => {
    const total = summary.timeseries.points.reduce(
      (sum, point) => sum + (point.new_identities[v.key] ?? 0),
      0,
    )
    return {
      colour: v.colour,
      key: v.key,
      name: v.name,
      share: headline === 0 ? 0 : total / headline,
      total,
    }
  })
}
