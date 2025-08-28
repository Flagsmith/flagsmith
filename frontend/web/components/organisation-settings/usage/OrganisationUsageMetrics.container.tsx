import React, { useMemo } from 'react'
import { Res } from 'common/types/responses'
import SingleSDKLabelsChart from './components/SingleSDKLabelsChart'

export interface OrganisationUsageMetricsProps {
  data?: Res['organisationUsage']
  selectedMetrics: string[]
}
export type ChartDataPoint = {
  day: any
} & Record<string, number>

const OrganisationUsageMetrics: React.FC<OrganisationUsageMetricsProps> = ({
  data,
  selectedMetrics,
}) => {
  const colours = [
    'rgba(37, 99, 235, 0.8)',
    'rgba(220, 38, 38, 0.8)',
    'rgba(22, 163, 74, 0.8)',
    'rgba(234, 88, 12, 0.8)',
    'rgba(124, 58, 237, 0.8)',
    'rgba(8, 145, 178, 0.8)',
    'rgba(219, 39, 119, 0.8)',
    'rgba(132, 204, 22, 0.8)',
    'rgba(245, 158, 11, 0.8)',
    'rgba(139, 92, 246, 0.8)',
    'rgba(6, 182, 212, 0.8)',
    'rgba(244, 114, 182, 0.8)',
    'rgba(16, 185, 129, 0.8)',
    'rgba(249, 115, 22, 0.8)',
    'rgba(99, 102, 241, 0.8)',
    'rgba(239, 68, 68, 0.8)',
    'rgba(34, 197, 94, 0.8)',
    'rgba(168, 85, 247, 0.8)',
    'rgba(20, 184, 166, 0.8)',
    'rgba(234, 179, 8, 0.8)',
  ]
  const {
    environmentDocumentChartData,
    flagsChartData,
    identitiesChartData,
    traitsChartData,
  } = useMemo(() => {
    if (!data?.events_list)
      return {
        environmentDocumentChartData: [],
        flagsChartData: [],
        identitiesChartData: [],
        traitsChartData: [],
      }

    const flagsGrouped: Record<string, ChartDataPoint> = {}
    const identitiesGrouped: Record<string, ChartDataPoint> = {}
    const environmentDocumentGrouped: Record<string, ChartDataPoint> = {}
    const traitsGrouped: Record<string, ChartDataPoint> = {}

    data.events_list.forEach((event) => {
      const date = event.day
      const userAgent = event.labels?.user_agent || 'Unknown'

      if (!flagsGrouped[date])
        flagsGrouped[date] = { day: date } as ChartDataPoint
      if (!identitiesGrouped[date])
        identitiesGrouped[date] = { day: date } as ChartDataPoint
      if (!environmentDocumentGrouped[date])
        environmentDocumentGrouped[date] = { day: date } as ChartDataPoint
      if (!traitsGrouped[date])
        traitsGrouped[date] = { day: date } as ChartDataPoint

      flagsGrouped[date][userAgent] =
        (flagsGrouped[date][userAgent] || 0) + (event.flags || 0)
      identitiesGrouped[date][userAgent] =
        (identitiesGrouped[date][userAgent] || 0) + (event.identities || 0)
      environmentDocumentGrouped[date][userAgent] =
        (environmentDocumentGrouped[date][userAgent] || 0) +
        (event.environment_document || 0)
      traitsGrouped[date][userAgent] =
        (traitsGrouped[date][userAgent] || 0) + (event.traits || 0)
    })

    return {
      environmentDocumentChartData: Object.values(environmentDocumentGrouped),
      flagsChartData: Object.values(flagsGrouped),
      identitiesChartData: Object.values(identitiesGrouped),
      traitsChartData: Object.values(traitsGrouped),
    }
  }, [data?.events_list])

  const userAgents = useMemo(() => {
    if (!data?.events_list) return []
    return [
      ...new Set(
        data.events_list.map((e) => e.labels?.user_agent || 'Unknown'),
      ),
    ]
  }, [data?.events_list])

  const chartItems = [
    {
      data: flagsChartData,
      metricKey: 'flags',
      title: 'Flags',
      userAgents,
      visible: selectedMetrics?.includes('Flags'),
    },
    {
      data: identitiesChartData,
      metricKey: 'identities',
      title: 'Identities',
      userAgents,
      visible: selectedMetrics?.includes('Identities'),
    },
    {
      data: environmentDocumentChartData,
      metricKey: 'environmentDocuments',
      title: 'Environment Documents',
      userAgents,
      visible: selectedMetrics?.includes('Environment Document'),
    },
    {
      data: traitsChartData,
      metricKey: 'traits',
      title: 'Traits',
      userAgents,
      visible: selectedMetrics?.includes('Traits'),
    },
  ]

  return (
    <div className='row'>
      {chartItems
        .filter((chart) => chart.visible)
        .map((chart) => (
          <div className='col-12 mb-4' key={chart.metricKey}>
            <SingleSDKLabelsChart
              data={chart.data}
              userAgents={chart.userAgents}
              metricKey={chart.metricKey}
              title={chart.title}
              colours={colours}
            />
          </div>
        ))}
    </div>
  )
}

export default OrganisationUsageMetrics
