import { CHART_COLOURS } from 'common/theme/tokens'

/**
 * Build a label → colour map using the chart palette, for `<BarChart>`'s
 * `colorMap` prop (and any other consumer that wants series-matched swatches
 * alongside the chart, e.g. a MultiSelect filter).
 *
 * Colours are CSS value strings (`var(--color-chart-N, #hex)`) — they resolve
 * at render time and react to theme changes via the CSS cascade. No hook,
 * no DOM read.
 *
 * Wraps around when there are more labels than colours.
 */
export function buildChartColorMap(labels: string[]): Record<string, string> {
  const map: Record<string, string> = {}
  labels.forEach((label, i) => {
    map[label] = CHART_COLOURS[i % CHART_COLOURS.length]
  })
  return map
}
