import { useMemo } from 'react'
import Color from 'color'
import Utils from 'common/utils/utils'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'

type UseEnvChartPropsArgs = {
  projectId: string
  environmentIds: string[]
}

type UseEnvChartPropsResult = {
  /** Selected env ids sorted by their position in the project's env list. */
  series: string[]
  /** env id → CSS colour matching the env tag chip colour. */
  colorMap: Record<string, string>
  /** env id → human-readable env name (for tooltip / legend display). */
  seriesLabels: Record<string, string>
}

/**
 * Chart-series config for environment-grouped charts.
 *
 * Resolves every value recharts needs per env: its colour (mirroring the env
 * tag chip via `Utils.getTagColour(indexInProjectEnvList)`), its display
 * name (for the tooltip), and a stable sort order (project-list position so
 * stack order doesn't shift with selection order).
 *
 * Reusable by any env-grouped chart — this hook is the single source of env
 * chart styling so new consumers (e.g. legacy `OrganisationUsage`) stay
 * visually consistent with feature analytics without duplicating logic.
 */
export function useEnvChartProps({
  environmentIds,
  projectId,
}: UseEnvChartPropsArgs): UseEnvChartPropsResult {
  const { data: environments } = useGetEnvironmentsQuery({
    projectId: Number(projectId),
  })

  return useMemo(() => {
    const envList = environments?.results ?? []
    const series = [...environmentIds].sort(
      (a, b) =>
        envList.findIndex((e) => `${e.id}` === a) -
        envList.findIndex((e) => `${e.id}` === b),
    )

    const colorMap: Record<string, string> = {}
    const seriesLabels: Record<string, string> = {}
    series.forEach((id) => {
      let index = envList.findIndex((e) => `${e.id}` === id)
      if (index === -1) index = 0
      colorMap[id] = `${Color(Utils.getTagColour(index)).alpha(0.75).rgb()}`
      const env = envList.find((e) => `${e.id}` === id)
      if (env) seriesLabels[id] = env.name
    })

    return { colorMap, series, seriesLabels }
  }, [environmentIds, environments?.results])
}
