import React, { FC } from 'react'
import { MetricItem, getFilteredOrganisationMetrics, getFilteredProjectMetrics, Filters } from '../services'
import MetricCard from './MetricCard'
import SectionHeader from './SectionHeader'
import EmptyState from 'components/base/EmptyState'

interface MetricsOverviewProps {
  context: 'organisation' | 'project'
  contextId: string
  filters?: Filters
  className?: string
}

const MetricsOverview: FC<MetricsOverviewProps> = ({ 
  context, 
  contextId, 
  filters, 
  className = '' 
}) => {
  // Use filtered data based on context and filters
  const getMetrics = (): MetricItem[] => {
    if (!filters) {
      // Fallback to default data if no filters provided
      return context === 'organisation' ? getFilteredOrganisationMetrics({
        timeRange: { startDate: null, endDate: null },
        projectId: undefined,
        environmentId: undefined
      }) : getFilteredProjectMetrics({
        timeRange: { startDate: null, endDate: null },
        projectId: contextId,
        environmentId: undefined
      })
    }
    
    if (context === 'organisation') {
      return getFilteredOrganisationMetrics(filters)
    } else {
      return getFilteredProjectMetrics(filters)
    }
  }

  const metrics = getMetrics()

  // Check if we have data
  const hasData = metrics && metrics.length > 0

  if (!hasData) {
    return (
      <div className={`mb-5 ${className}`}>
        <div className='card border-0 shadow-sm'>
          <div className='card-body py-5'>
            <EmptyState
              title="No Data Available"
              description="No metrics data available for the selected filters. Try adjusting your time range or project selection."
              icon="bar-chart"
              marginTop="0"
            />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`${className}`}>
      <SectionHeader
        title={context === 'organisation' ? 'Organization Overview' : 'Project Overview'}
        description={context === 'organisation' 
          ? 'Key metrics across all your projects' 
          : 'Key metrics for this project'}
      />
      
      {/* Metrics Grid */}
      <div className='row g-3'>
        {metrics.map((metric) => (
          <div key={metric.name} className='col-lg-3 col-md-4 col-sm-6'>
            <MetricCard 
              metric={metric}
              className='h-100'
              showCardWrapper={true}
              textAlign="text-center"
            />
          </div>
        ))}
      </div>
    </div>
  )
}

export default MetricsOverview
