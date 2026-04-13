import { CHART_COLOURS } from 'common/theme/tokens'

/**
 * Build a label → colour map using the chart palette.
 *
 * Colours are CSS value strings (`var(--color-chart-N, #hex)`) — they resolve
 * at render time and react to theme changes via the CSS cascade. No hook,
 * no DOM read.
 *
 * Wraps around when there are more labels than colours.
 */
export function buildChartColorMap(labels: string[]): Map<string, string> {
  const map = new Map<string, string>()
  labels.forEach((label, i) => {
    map.set(label, CHART_COLOURS[i % CHART_COLOURS.length])
  })
  return map
}
