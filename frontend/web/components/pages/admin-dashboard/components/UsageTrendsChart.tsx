import { FC } from 'react'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import moment from 'moment'
import { UsageTrend } from 'common/types/responses'
import Utils from 'common/utils/utils'
import Card from 'components/Card'

interface UsageTrendsChartProps {
  trends: UsageTrend[]
  days?: number
}

const UsageTrendsChart: FC<UsageTrendsChartProps> = ({ days = 30, trends }) => {
  const chartData = trends.map((trend) => ({
    ...trend,
    date: moment(trend.date).format('MMM DD'),
  }))

  return (
    <Card className='shadow p-4'>
      <h5 className='mb-4 mt-2'>API Usage Trends (Last {days} Days)</h5>
      <div style={{ height: 340, marginTop: 16 }}>
        <ResponsiveContainer width='100%' height='100%'>
          <LineChart
            data={chartData}
            margin={{ bottom: 10, left: 10, right: 10, top: 10 }}
          >
            <CartesianGrid strokeDasharray='3 3' />
            <XAxis
              dataKey='date'
              tick={{ fontSize: 12 }}
              interval='preserveStartEnd'
            />
            <YAxis
              tickFormatter={(value: number) => Utils.numberWithCommas(value)}
              tick={{ fontSize: 12 }}
            />
            <Tooltip
              formatter={(value: number) => Utils.numberWithCommas(value)}
            />
            <Legend />
            <Line
              type='monotone'
              dataKey='api_calls'
              name='API Calls'
              stroke='#0AADDF'
              strokeWidth={2}
              dot={false}
            />
            <Line
              type='monotone'
              dataKey='flag_evaluations'
              name='Flag Evaluations'
              stroke='#27AB95'
              strokeWidth={2}
              dot={false}
            />
            <Line
              type='monotone'
              dataKey='identity_requests'
              name='Identity Requests'
              stroke='#FF9F43'
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}

export default UsageTrendsChart
