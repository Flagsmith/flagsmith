import React, { FC } from 'react'
import BarChart, { ChartDataPoint } from 'components/charts/BarChart'
import EmptyState from 'components/EmptyState'
import Text from 'components/base/Text'

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
      <Text variant='h5' level={2}>
        {title}
      </Text>
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
