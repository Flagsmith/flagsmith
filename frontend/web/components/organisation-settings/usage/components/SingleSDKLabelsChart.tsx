import React, { FC } from 'react'
import BarChart from 'components/charts/BarChart'
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
}) => (
  <div className='border rounded p-3'>
    <h5>{title}</h5>
    <BarChart
      data={data}
      series={userAgents}
      colorMap={userAgentsColorMap}
      xAxisInterval={data?.length > 31 ? 7 : 0}
      showLegend
    />
  </div>
)

export default SingleSDKLabelsChart
