export type ChartDataPoint = {
  day: string
  [key: string]: string | number | null
}

/**
 * One line on a chart. Keyed by the field it reads from `ChartDataPoint`,
 * carrying everything that used to live in a map beside it.
 */
export type ChartSeries = {
  key: string
  label?: string
  colour: string
  dashed?: boolean
  /** False where adding this to the others means nothing, as for a running total. */
  summable?: boolean
}

/**
 * Build series from the parallel maps a caller already has. For consumers
 * that derive their colours and labels elsewhere; prefer describing the
 * series directly.
 */
export const seriesFromMaps = (
  keys: readonly string[],
  colours: Record<string, string>,
  labels?: Record<string, string>,
): ChartSeries[] =>
  keys.map((key) => ({ colour: colours[key], key, label: labels?.[key] }))
