import React, { FC, useMemo } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { getChartConfig, getChartColorPalette } from '../utils/chartColors'
import moment from 'moment'
import { ActivityDataPoint } from '../services'
import SectionHeader from './SectionHeader'

interface ActivityChartProps {
  activityData: ActivityDataPoint[]
  className?: string
}

const ActivityChart: FC<ActivityChartProps> = ({
  activityData,
  className = ''
}) => {
  // Transform data for chart display with smart date formatting
  const chartData = useMemo(() => {
    const getDateFormat = (data: ActivityDataPoint[]) => {
      if (data.length <= 7) {
        return 'MMM D' // Daily: Jan 1
      } else if (data.length <= 12) {
        return 'MMM D' // Weekly: Jan 1
      } else {
        return 'MMM YY' // Monthly: Jan 24
      }
    }

    const dateFormat = getDateFormat(activityData)
    
    return activityData.map(item => ({
      day: moment(item.date).format(dateFormat),
      date: item.date,
      'Features Created': item.features_created,
      'Features Updated': item.features_updated,
      'Features Deleted': item.features_deleted,
      'Change Requests': item.change_requests_committed,
    }))
  }, [activityData])

  // Get theme-aware chart configuration
  const chartConfig = useMemo(() => getChartConfig(), [])
  const colorPalette = useMemo(() => getChartColorPalette(4), [])

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div 
          className='bg-white p-3 border rounded shadow-lg reporting-chart-container'
        >
          <p className='fw-semibold mb-3 reporting-chart-label'>
            {label}
          </p>
          <div className='d-flex flex-column gap-2'>
            {payload.map((entry: any, index: number) => (
              <div key={index} className='d-flex align-items-center justify-content-between'>
                <div className='d-flex align-items-center gap-2'>
                  <div 
                    className='reporting-chart-legend-dot'
                    style={{ backgroundColor: entry.color }}
                  ></div>
                  <span className='reporting-chart-entry-name'>
                    {entry.name}
                  </span>
                </div>
                <span className='fw-semibold reporting-chart-entry-value'>
                  {entry.value}
                </span>
              </div>
            ))}
          </div>
        </div>
      )
    }
    return null
  }

  if (!activityData || activityData.length === 0) {
    return (
      <div className={`text-center py-4 ${className}`}>
        <p className='text-muted'>No activity data available for the selected time period.</p>
      </div>
    )
  }

  return (
    <div className={`${className}`}>
      <SectionHeader 
        title="Activity Trends"
        description="Feature activity over time"
        className="mb-3"
      />
      
      <ResponsiveContainer height={300} width='100%'>
        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
          <CartesianGrid {...chartConfig.gridProps} />
          <XAxis
            dataKey='day'
            {...chartConfig.xAxisProps}
            angle={chartData.length > 20 ? -45 : 0}
            textAnchor={chartData.length > 20 ? 'end' : 'middle'}
            height={chartData.length > 20 ? 80 : 60}
            interval={chartData.length > 30 ? 'preserveStartEnd' : 0}
          />
          <YAxis
            {...chartConfig.yAxisProps}
          />
          <RechartsTooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0, 0, 0, 0.05)' }} />
          <Bar 
            dataKey='Features Created' 
            stackId='a' 
            fill={colorPalette[0]} 
            barSize={chartData.length > 30 ? 8 : chartData.length > 12 ? 12 : 16}
          />
          <Bar 
            dataKey='Features Updated' 
            stackId='a' 
            fill={colorPalette[1]} 
            barSize={chartData.length > 30 ? 8 : chartData.length > 12 ? 12 : 16}
          />
          <Bar 
            dataKey='Features Deleted' 
            stackId='a' 
            fill={colorPalette[2]} 
            barSize={chartData.length > 30 ? 8 : chartData.length > 12 ? 12 : 16}
          />
          <Bar 
            dataKey='Change Requests' 
            stackId='a' 
            fill={colorPalette[3]} 
            barSize={chartData.length > 30 ? 8 : chartData.length > 12 ? 12 : 16}
          />
        </BarChart>
      </ResponsiveContainer>
      <div className='d-flex justify-content-center gap-4 mt-3 flex-wrap'>
        <div className='d-flex align-items-center gap-2'>
          <div 
            className='reporting-chart-legend-dot' 
            style={{ backgroundColor: colorPalette[0] }}
          ></div>
          <span className='small reporting-chart-legend-text'>Created</span>
        </div>
        <div className='d-flex align-items-center gap-2'>
          <div 
            className='reporting-chart-legend-dot' 
            style={{ backgroundColor: colorPalette[1] }}
          ></div>
          <span className='small reporting-chart-legend-text'>Updated</span>
        </div>
        <div className='d-flex align-items-center gap-2'>
          <div 
            className='reporting-chart-legend-dot' 
            style={{ backgroundColor: colorPalette[2] }}
          ></div>
          <span className='small reporting-chart-legend-text'>Deleted</span>
        </div>
        <div className='d-flex align-items-center gap-2'>
          <div 
            className='reporting-chart-legend-dot' 
            style={{ backgroundColor: colorPalette[3] }}
          ></div>
          <span className='small reporting-chart-legend-text'>Change Requests</span>
        </div>
      </div>
    </div>
  )
}

export default ActivityChart
