import React, { FC } from 'react'
import BarChart from 'components/charts/BarChart'
import EmptyState from 'components/EmptyState'
import { ChartDataPoint } from 'components/organisation-settings/usage/OrganisationUsageMetrics.container'

interface SingleSDKLabelsChartProps {
  title: string
  data: ChartDataPoint[]
  userAgents?: string[]
  userAgentsColorMap: Record<string, string>
}

const SingleSDKLabelsChart: FC<SingleSDKLabelsChartProps> = ({
  data,
  title,
  userAgents = [],
  userAgentsColorMap,
}) => {
  const hasData = data.length > 0 && userAgents.length > 0

  return (
    <div className='border rounded p-3'>
      <h5>{title}</h5>
      {hasData ? (
        <BarChart
          data={data}
          series={userAgents}
          colorMap={userAgentsColorMap}
          xAxisInterval={data?.length > 31 ? 7 : 0}
          showLegend
        />
      ) : (
        <EmptyState
          title='No SDK data'
          description='No SDK usage data available for the selected period.'
          icon='bar-chart'
        />
      )}
    </div>
  )
}

export default SingleSDKLabelsChart
