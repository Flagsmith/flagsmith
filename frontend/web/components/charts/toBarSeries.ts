import { BarSeries } from './types'

/**
 * Bridge for callers that hold the older parallel maps (a `buildChartColorMap`
 * result, `useEnvChartProps`, anything shared with `LineChart`). New callers
 * should build `BarSeries` objects directly.
 */
export const toBarSeries = (
  keys: string[],
  colorMap: Record<string, string>,
  seriesLabels?: Record<string, string>,
): BarSeries[] =>
  keys.map((key) => ({
    colour: colorMap[key],
    key,
    label: seriesLabels?.[key] ?? key,
  }))
