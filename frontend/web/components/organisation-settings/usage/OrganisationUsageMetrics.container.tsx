import React, { useMemo, useState } from 'react'
import moment from 'moment'
import { Res } from 'common/types/responses'
import SingleSDKLabelsChart from './components/SingleSDKLabelsChart'
import { MultiSelect } from 'components/base/select/multi-select'

interface OrganisationUsageMetricsProps {
  data?: Res['organisationUsage']
  selectedMetrics: string[]
}
export type ChartDataPoint = {
  day: string
} & Record<string, number>

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

const OrganisationUsageMetrics: React.FC<OrganisationUsageMetricsProps> = ({
  data,
  selectedMetrics,
}) => {
  const [selectedUserAgents, setSelectedUserAgents] = useState<string[]>([])

  const { aggregateChartData, allUserAgents, userAgentColorMap } =
    useMemo(() => {
      if (!data?.events_list)
        return {
          aggregateChartData: [],
          allUserAgents: [],
          userAgentColorMap: {} as Record<string, string>,
        }

      const aggregateGrouped: Record<string, ChartDataPoint> = {}
      const userAgents: string[] = []
      const userAgentSet = new Set<string>()

      data.events_list.forEach((event) => {
        // BarChart consumes the displayed day string as the x-axis dataKey,
        // so format here once and let the chart use it verbatim.
        const date = moment(event.day).format('D MMM')
        const userAgent = event.labels?.user_agent || 'Unknown'

        if (!userAgentSet.has(userAgent)) {
          userAgentSet.add(userAgent)
          userAgents.push(userAgent)
        }

        if (!aggregateGrouped[date])
          aggregateGrouped[date] = { day: date } as ChartDataPoint

        let totalForUserAgent = 0
        if (selectedMetrics.includes('Flags'))
          totalForUserAgent += event.flags || 0
        if (selectedMetrics.includes('Identities'))
          totalForUserAgent += event.identities || 0
        if (selectedMetrics.includes('Environment Document'))
          totalForUserAgent += event.environment_document || 0
        if (selectedMetrics.includes('Traits'))
          totalForUserAgent += event.traits || 0

        aggregateGrouped[date][userAgent] =
          (aggregateGrouped[date][userAgent] || 0) + totalForUserAgent
      })

      const colorMap: Record<string, string> = {}
      userAgents.forEach((agent, index) => {
        colorMap[agent] = colours[index % colours.length]
      })

      return {
        aggregateChartData: Object.values(aggregateGrouped),
        allUserAgents: userAgents,
        userAgentColorMap: colorMap,
      }
    }, [data?.events_list, selectedMetrics])

  const userAgentOptions = useMemo(() => {
    return allUserAgents.map((agent) => ({
      label: agent,
      value: agent,
    }))
  }, [allUserAgents])

  const filteredUserAgents =
    selectedUserAgents.length > 0
      ? allUserAgents.filter((userAgent) =>
          selectedUserAgents.includes(userAgent),
        )
      : allUserAgents

  return (
    <div className='row'>
      <div className='col-12 mb-4'>
        <div className='row'>
          <div className='col-12'>
            <MultiSelect
              label='Filter SDKs'
              options={userAgentOptions}
              selectedValues={selectedUserAgents}
              onSelectionChange={setSelectedUserAgents}
              colorMap={userAgentColorMap}
            />
          </div>
        </div>
      </div>
      <div className='col-12 mb-4'>
        <SingleSDKLabelsChart
          data={aggregateChartData}
          userAgents={filteredUserAgents}
          title='API Usage'
          userAgentsColorMap={userAgentColorMap}
        />
      </div>
    </div>
  )
}

export default OrganisationUsageMetrics
