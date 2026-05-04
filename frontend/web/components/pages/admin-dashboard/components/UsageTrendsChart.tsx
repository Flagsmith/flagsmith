import { FC, useMemo } from 'react'
import moment from 'moment'
import { UsageTrend } from 'common/types/responses'
import Card from 'components/Card'
import {
  buildChartColorMap,
  ChartDataPoint,
  LineChart,
} from 'components/charts'

interface UsageTrendsChartProps {
  trends: UsageTrend[]
  days?: number
}

const SERIES = ['api_calls', 'flag_evaluations', 'identity_requests'] as const

const SERIES_LABELS: Record<string, string> = {
  api_calls: 'API Calls',
  flag_evaluations: 'Flag Evaluations',
  identity_requests: 'Identity Requests',
}

const UsageTrendsChart: FC<UsageTrendsChartProps> = ({ days = 30, trends }) => {
  const data = useMemo<ChartDataPoint[]>(
    () =>
      trends.map((trend) => ({
        api_calls: trend.api_calls,
        day: moment(trend.date).format('MMM DD'),
        flag_evaluations: trend.flag_evaluations,
        identity_requests: trend.identity_requests,
      })),
    [trends],
  )

  const colorMap = useMemo(() => buildChartColorMap([...SERIES]), [])

  return (
    <Card className='shadow p-4'>
      <h5 className='mb-4 mt-2'>API Usage Trends (Last {days} Days)</h5>
      <LineChart
        data={data}
        series={[...SERIES]}
        colorMap={colorMap}
        seriesLabels={SERIES_LABELS}
        xAxisInterval={2}
        showLegend
      />
    </Card>
  )
}

export default UsageTrendsChart
