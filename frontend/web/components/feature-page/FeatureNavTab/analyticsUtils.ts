import { ChartDataPoint } from 'components/charts/BarChart'
import { Res } from 'common/types/responses'
import { CHART_COLOURS } from 'common/theme/tokens'
import { getCSSVars } from 'common/utils/getCSSVar'

/**
 * Check if the analytics data contains labelled buckets.
 */
export function hasLabelledData(
  rawData: Res['environmentAnalytics'] | undefined,
): boolean {
  if (!rawData) return false
  return rawData.some(
    (entry) => entry.labels && Object.keys(entry.labels).length > 0,
  )
}

/**
 * Aggregate raw environment analytics into label-grouped chart data.
 * Each unique label value becomes a series in the stacked chart.
 */
export function aggregateByLabels(rawData: Res['environmentAnalytics']): {
  chartData: ChartDataPoint[]
  colorMap: Map<string, string>
  labelValues: string[]
} {
  const grouped: Record<string, ChartDataPoint> = {}
  const labelSet = new Set<string>()
  const labelList: string[] = []

  rawData.forEach((entry) => {
    const date = entry.day
    const labelValue =
      entry.labels?.user_agent ||
      entry.labels?.client_application_name ||
      'Unknown'

    if (!labelSet.has(labelValue)) {
      labelSet.add(labelValue)
      labelList.push(labelValue)
    }

    if (!grouped[date]) {
      grouped[date] = { day: date }
    }
    grouped[date][labelValue] = (grouped[date][labelValue] || 0) + entry.count
  })

  const resolvedColors = getCSSVars(CHART_COLOURS)
  const colorMap = new Map<string, string>()
  labelList.forEach((label, index) => {
    colorMap.set(label, resolvedColors[index % resolvedColors.length])
  })

  return {
    chartData: Object.values(grouped),
    colorMap,
    labelValues: labelList,
  }
}

/**
 * Build a color map for environment-based (non-labelled) chart mode.
 */
export function buildEnvColorMap(
  environmentIds: string[],
): Map<string, string> {
  const resolvedColors = getCSSVars(CHART_COLOURS)
  const map = new Map<string, string>()
  environmentIds.forEach((id, index) => {
    map.set(id, resolvedColors[index % resolvedColors.length])
  })
  return map
}
