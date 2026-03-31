function resolveToken(cssVar: string): string {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(cssVar)
    .trim()
}

type ChartTheme = {
  gridStroke: string
  tickFill: string
  axisStroke: string
  tooltipLabelColour: string
  lineInfo: string
  lineSuccess: string
  lineWarning: string
  lineDanger: string
  lineAction: string
  variantColours: string[]
  winnerColour: string
}

export default function useChartTheme(): ChartTheme {
  const action = resolveToken('--color-text-action')
  const info = resolveToken('--color-text-info')
  const success = resolveToken('--color-text-success')
  const warning = resolveToken('--color-text-warning')
  const danger = resolveToken('--color-text-danger')

  return {
    axisStroke: resolveToken('--color-border-default'),
    gridStroke: resolveToken('--color-border-default'),
    lineAction: action,
    lineDanger: danger,
    lineInfo: info,
    lineSuccess: success,
    lineWarning: warning,
    tickFill: resolveToken('--color-text-secondary'),
    tooltipLabelColour: resolveToken('--color-text-default'),
    variantColours: [action, info, warning, danger, success],
    winnerColour: success,
  }
}
