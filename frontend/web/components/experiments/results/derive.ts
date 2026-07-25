import moment from 'moment'
import { ChartDataPoint, buildChartColorMap } from 'components/charts'
import { colorTextDanger, colorTextSuccess } from 'common/theme/tokens'
import {
  BayesianMetricResult,
  BayesianResultsSummary,
  Experiment,
  ExperimentFeature,
  ExposureGranularity,
  ExposuresSummary,
  Inference,
  MultivariateOption,
} from 'common/types/responses'
import { getPrimaryMetric } from 'components/experiments/constants'

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

export const getResultsTotalUsers = (
  results: BayesianResultsSummary,
): number => {
  const firstMetric = results.metrics[0]
  if (!firstMetric) return 0
  return Object.values(firstMetric.variants).reduce((sum, v) => sum + v.n, 0)
}

// Colour by sign only — expected_direction is not used reliably yet, so it
// deliberately plays no part in lift colouring.
export const isLiftFavourable = (lift: number): boolean => lift > 0

export const getLiftColour = (lift: number): string =>
  isLiftFavourable(lift) ? colorTextSuccess : colorTextDanger

export const formatLiftPct = (lift: number): string => {
  const pct = lift * 100
  return `${pct >= 0 ? '+' : ''}${pct.toFixed(1)}%`
}

export const getMetricResult = (
  results: BayesianResultsSummary,
  metricId: number,
): BayesianMetricResult | undefined =>
  results.metrics.find((m) => m.metric_id === metricId)

export type WinningVariant = {
  key: string
  name: string
  chanceToWin: number
  inference: Inference | null
  isControl: boolean
}

// chance_to_win is pairwise — P(variant beats control) — so chances don't sum
// to 1 across arms. P(control is best) = P(no variant beats it); the Bonferroni
// bound 1 - Σ chance_to_win is exact for one variant, conservative otherwise.
export const getWinningVariant = (
  metricResult: BayesianMetricResult,
  identities: VariantIdentity[],
): WinningVariant | null => {
  let best: WinningVariant | null = null
  let treatmentChancesTotal = 0
  for (const v of identities) {
    if (v.isControl) continue
    const inf = metricResult.inference[v.key]
    if (!inf) continue
    treatmentChancesTotal += inf.chance_to_win
    if (!best || inf.chance_to_win > best.chanceToWin) {
      best = {
        chanceToWin: inf.chance_to_win,
        inference: inf,
        isControl: false,
        key: v.key,
        name: v.name,
      }
    }
  }
  if (!best) return null
  const control = identities.find((v) => v.isControl)
  const controlChance = Math.max(0, 1 - treatmentChancesTotal)
  if (control && controlChance > best.chanceToWin) {
    return {
      chanceToWin: controlChance,
      inference: null,
      isControl: true,
      key: control.key,
      name: control.name,
    }
  }
  return best
}

export type SummaryStats = {
  winnerName: string
  winnerColour: string
  controlColour: string
  controlWins: boolean
  chanceToBest: string
  liftVsControl: string
  liftFavourable: boolean
}

export const deriveSummary = (
  experiment: Experiment,
  results: BayesianResultsSummary,
): SummaryStats | null => {
  const metric = getPrimaryMetric(experiment)
  if (!metric) return null
  const metricResult = getMetricResult(results, metric.metric)
  if (!metricResult) return null

  const identities = getVariantIdentities(experiment.feature)
  const winner = getWinningVariant(metricResult, identities)
  if (!winner) return null

  const winnerIdentity = identities.find((v) => v.key === winner.key)
  const controlIdentity = identities.find((v) => v.isControl)

  return {
    chanceToBest: `${Math.round(winner.chanceToWin * 100)}%`,
    controlColour: controlIdentity?.colour ?? '',
    controlWins: winner.isControl,
    liftFavourable: winner.inference
      ? isLiftFavourable(winner.inference.lift)
      : false,
    liftVsControl: winner.inference
      ? formatLiftPct(winner.inference.lift)
      : 'Baseline',
    winnerColour: winnerIdentity?.colour ?? '',
    winnerName: winner.name,
  }
}

export type AxisRange = { min: number; max: number }

export const computeAxisRange = (
  identities: VariantIdentity[],
  metricResult?: BayesianMetricResult,
): AxisRange => {
  let min = -0.1
  let max = 0.1
  identities.forEach((v) => {
    if (v.isControl) return
    const inf = metricResult?.inference[v.key]
    if (!inf) return
    if (inf.ci_low < min) min = inf.ci_low
    if (inf.ci_high > max) max = inf.ci_high
  })
  const pad = (max - min) * 0.15
  return { max: max + pad, min: min - pad }
}

export const valueToPercent = (value: number, range: AxisRange): number =>
  ((value - range.min) / (range.max - range.min)) * 100

export const buildTicks = (range: AxisRange): number[] => {
  const span = range.max - range.min
  let step = 0.05
  if (span > 5) step = 1
  else if (span > 2) step = 0.5
  else if (span > 0.6) step = 0.2
  else if (span > 0.3) step = 0.1

  const ticks: number[] = []
  const start = Math.ceil(range.min / step) * step
  for (let v = start; v <= range.max; v += step) {
    ticks.push(Math.round(v * 1000) / 1000)
  }
  return ticks
}

export const liftToPercent = (value: number, liftRange: number): number =>
  Math.max(0, Math.min(100, ((value / liftRange + 1) / 2) * 100))

export const computeLiftRange = (
  identities: VariantIdentity[],
  metricResult?: BayesianMetricResult,
): number => {
  let max = 0.3
  identities.forEach((v) => {
    if (v.isControl) return
    const inf = metricResult?.inference[v.key]
    if (!inf) return
    max = Math.max(max, Math.abs(inf.ci_low), Math.abs(inf.ci_high))
  })
  return max * 1.1
}

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
