import { useMemo } from 'react'
import { CHART_COLOURS } from 'common/theme/tokens'

/**
 * Reads the computed value of CSS custom properties from the document root.
 *
 * Why not import values directly from tokens.ts?
 * tokens.ts exports CSS var() references (e.g. 'var(--color-chart-1, #0aaddf)'),
 * not raw hex strings. Recharts' `fill` prop needs actual colour values like
 * '#0aaddf', not var() references. getComputedStyle resolves the var to its
 * current value, which also means dark mode is respected automatically —
 * the same token resolves to a different hex in light vs dark.
 */
function resolveColors(varNames: readonly string[]): string[] {
  if (typeof document === 'undefined') return varNames.map(() => '')
  const style = getComputedStyle(document.documentElement)
  return varNames.map((name) => style.getPropertyValue(name).trim())
}

/**
 * Returns the resolved chart color palette for the current theme.
 *
 * @example
 *   const colors = useChartColors()
 *   colors[0] // '#0aaddf' in light, '#45bce0' in dark
 */
export function useChartColors(): string[] {
  return useMemo(() => resolveColors(CHART_COLOURS), [])
}

/**
 * Builds a color map from a list of series names to chart colors.
 * Wraps around when there are more series than available colors.
 *
 * @example
 *   const colorMap = useChartColorMap(['js-sdk', 'python-sdk'])
 *   colorMap.get('js-sdk') // '#0aaddf'
 */
export function useChartColorMap(series: string[]): Map<string, string> {
  const colors = useChartColors()
  return useMemo(() => {
    const map = new Map<string, string>()
    series.forEach((name, index) => {
      map.set(name, colors[index % colors.length])
    })
    return map
  }, [series, colors])
}
