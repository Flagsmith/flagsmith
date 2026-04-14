import moment from 'moment'
import { ChartDataPoint } from 'components/charts/BarChart'
import { Res } from 'common/types/responses'
import { buildChartColorMap } from 'components/charts/buildChartColorMap'

/**
 * Check if the analytics data contains usable labels.
 *
 * Returns true only when at least one entry has a non-empty `user_agent` or
 * `client_application_name`. Backends sometimes return label keys with null
 * values (e.g. `{ user_agent: null }`); those don't count as labelled since
 * every entry would collapse to 'Unknown' in aggregation.
 */
export function hasLabelledData(
  rawData: Res['environmentAnalytics'] | undefined,
): boolean {
  if (!rawData) return false
  return rawData.some((entry) => {
    if (!entry.labels) return false
    return Boolean(
      entry.labels.user_agent || entry.labels.client_application_name,
    )
  })
}

/**
 * Aggregate raw environment analytics into label-grouped chart data.
 * Each unique label value becomes a series in the stacked chart.
 *
 * `days` must be the caller's pre-built day axis (in 'Do MMM' format, matching
 * `useFeatureAnalytics`'s env-path chartData). We seed the result with zero
 * buckets for every day so the x-axis stays complete and ordered even when
 * some days have no events.
 */
export function aggregateByLabels(
  rawData: Res['environmentAnalytics'],
  days: string[],
): {
  chartData: ChartDataPoint[]
  colorMap: Record<string, string>
  labelValues: string[]
} {
  const grouped: Record<string, ChartDataPoint> = {}
  days.forEach((day) => {
    grouped[day] = { day }
  })

  const labelSet = new Set<string>()
  const labelList: string[] = []

  rawData.forEach((entry) => {
    const day = moment(entry.day).format('Do MMM')
    // Priority: user_agent (SDK name) > client_application_name > 'Unknown'
    const labelValue =
      entry.labels?.user_agent ||
      entry.labels?.client_application_name ||
      'Unknown'

    if (!labelSet.has(labelValue)) {
      labelSet.add(labelValue)
      labelList.push(labelValue)
    }

    if (grouped[day]) {
      grouped[day][labelValue] = (grouped[day][labelValue] ?? 0) + entry.count
    }
  })

  return {
    chartData: days.map((day) => grouped[day]),
    colorMap: buildChartColorMap(labelList),
    labelValues: labelList,
  }
}
