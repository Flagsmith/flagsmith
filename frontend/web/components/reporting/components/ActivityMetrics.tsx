import React, { FC } from 'react'
import { getFilteredActivityData, Filters } from '../services'
import ActivityChart from './ActivityChart'
import SectionHeader from './SectionHeader'
import EmptyState from 'components/base/EmptyState'
import Card from './Card'

interface ActivityMetricsProps {
  context: 'organisation' | 'project'
  contextId: string
  filters?: Filters
  className?: string
}

const ActivityMetrics: FC<ActivityMetricsProps> = ({
  context,
  contextId,
  filters,
  className = ''
}) => {
  // Use filtered activity data based on context and filters
  const getActivityData = () => {
    if (!filters) {
      // Fallback to default data if no filters provided
      return getFilteredActivityData({
        timeRange: { startDate: null, endDate: null },
        projectId: context === 'project' ? contextId : undefined,
        environmentId: undefined
      }, context)
    }
    
    return getFilteredActivityData(filters, context)
  }

  const activityData = getActivityData()

  const totalCreated = activityData.reduce((sum, day) => sum + day.features_created, 0)
  const totalUpdated = activityData.reduce((sum, day) => sum + day.features_updated, 0)
  const totalDeleted = activityData.reduce((sum, day) => sum + day.features_deleted, 0)

  // Check if we have activity data
  const hasActivityData = activityData && activityData.length > 0 && (totalCreated > 0 || totalUpdated > 0 || totalDeleted > 0)

  if (!hasActivityData) {
    return (
      <div className={`${className}`}>
        <Card variant="default" className="shadow-sm">
          <EmptyState
            title="No Activity Data"
            description="No feature activity found for the selected time period. Try adjusting your filters or selecting a different time range."
            icon="trending-up"
            marginTop="0"
          />
        </Card>
      </div>
    )
  }

  // Calculate trend indicators (mock data for now)
  const getTrendIndicator = (current: number, previous: number) => {
    if (previous === 0) return { value: 0, isPositive: true }
    const change = ((current - previous) / previous) * 100
    return {
      value: Math.abs(change),
      isPositive: change >= 0
    }
  }

  // Mock previous period data for trend calculation
  const previousPeriodData = {
    created: Math.floor(totalCreated * 0.85), // 15% less than current
    updated: Math.floor(totalUpdated * 1.12), // 12% more than current
    deleted: Math.floor(totalDeleted * 0.92)  // 8% less than current
  }

  const createdTrend = getTrendIndicator(totalCreated, previousPeriodData.created)
  const updatedTrend = getTrendIndicator(totalUpdated, previousPeriodData.updated)
  const deletedTrend = getTrendIndicator(totalDeleted, previousPeriodData.deleted)

  return (
    <div className={`${className}`}>
      <div className='row g-3'>
        <div className='col-lg-5'>
          <Card variant="default" fullHeight={true}>
            <SectionHeader
              title="Activity Summary"
              description="Feature activity over the selected time period"
            />
              
              <div className='d-flex gap-3 justify-content-between'>
                <div className='text-center flex-fill'>
                  <div className='fw-bold mb-2 reporting-activity-label'>
                    Created
                  </div>
                  <div className='fw-bold mb-1 reporting-activity-value'>
                    {totalCreated}
                  </div>
                  <div className='d-flex align-items-center justify-content-center gap-1 reporting-trend-text'>
                    <span 
                      className={`fw-semibold ${createdTrend.isPositive ? 'text-success' : 'text-danger'}`}
                    >
                      {createdTrend.isPositive ? '+' : '-'}{createdTrend.value.toFixed(0)}%
                    </span>
                  </div>
                </div>

                <div className='text-center flex-fill'>
                  <div className='fw-bold mb-2 reporting-activity-label'>
                    Updated
                  </div>
                  <div className='fw-bold mb-1 reporting-activity-value'>
                    {totalUpdated}
                  </div>
                  <div className='d-flex align-items-center justify-content-center gap-1 reporting-trend-text'>
                    <span 
                      className={`fw-semibold ${updatedTrend.isPositive ? 'text-success' : 'text-danger'}`}
                    >
                      {updatedTrend.isPositive ? '+' : '-'}{updatedTrend.value.toFixed(0)}%
                    </span>
                  </div>
                </div>

                <div className='text-center flex-fill'>
                  <div className='fw-bold mb-2 reporting-activity-label'>
                    Deleted
                  </div>
                  <div className='fw-bold mb-1 reporting-activity-value'>
                    {totalDeleted}
                  </div>
                  <div className='d-flex align-items-center justify-content-center gap-1 reporting-trend-text'>
                    <span 
                      className={`fw-semibold ${deletedTrend.isPositive ? 'text-success' : 'text-danger'}`}
                    >
                      {deletedTrend.isPositive ? '+' : '-'}{deletedTrend.value.toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>
          </Card>
        </div>

        <div className='col-lg-7'>
          <Card variant="default" fullHeight={true}>
            <ActivityChart activityData={activityData} />
          </Card>
        </div>
      </div>
    </div>
  )
}

export default ActivityMetrics
