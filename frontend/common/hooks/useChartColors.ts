import { useMemo } from 'react'
import { CHART_COLOURS } from 'common/theme/tokens'
import { getCSSVars } from 'common/utils/getCSSVar'

/**
 * Returns the resolved chart color palette for the current theme.
 *
 * Recharts needs actual color strings (not CSS var references),
 * so this hook reads the computed values of --color-chart-1 through
 * --color-chart-10 from the document root.
 *
 * @example
 *   const colors = useChartColors()
 *   colors[0] // '#0aaddf' in light, '#45bce0' in dark
 */
export function useChartColors(): string[] {
  return useMemo(() => getCSSVars(CHART_COLOURS), [])
}

/**
 * Builds a color map from a list of series names to chart colors.
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
