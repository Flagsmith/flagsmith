import React, { FC, useState, useMemo } from 'react'
import { Filters, getPerformanceMetrics, getHealthMetrics } from '../services'
import MetricsOverview from './MetricsOverview'
import ActivityMetrics from './ActivityMetrics'
import SectionHeader from './SectionHeader'
import MetricCard from './MetricCard'
import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'
import Icon from 'components/Icon'

interface TabbedReportingDashboardProps {
  context: 'organisation' | 'project'
  contextId: string
  filters: Filters
  className?: string
}

const TabbedReportingDashboard: FC<TabbedReportingDashboardProps> = ({
  context,
  contextId,
  filters,
  className = ''
}) => {
  const [activeTab, setActiveTab] = useState(0)

  // Get performance and health metrics from mock data
  const performanceMetrics = useMemo(() => 
    getPerformanceMetrics(filters, context), [filters, context]
  )
  
  const healthMetrics = useMemo(() => 
    getHealthMetrics(filters, context), [filters, context]
  )

  const renderPerformanceContent = () => (
    <div>
      <SectionHeader
        title="Program Performance"
        description="Feature management program effectiveness and velocity metrics"
      />
      <div className='row g-3'>
        <div className='col-md-4'>
          <MetricCard
            title="Avg Time to Production (days)"
            value={performanceMetrics.avgTimeToProduction}
            variant="simple"
            showCardWrapper={true}
            textAlign="text-center"
          />
        </div>
        <div className='col-md-4'>
          <MetricCard
            title="Feature Utilization Rate"
            value={`${performanceMetrics.featureUtilizationRate}%`}
            variant="simple"
            showCardWrapper={true}
            textAlign="text-center"
          />
        </div>
        <div className='col-md-4'>
          <MetricCard
            title="Features per Week"
            value={performanceMetrics.featuresPerWeek}
            variant="simple"
            showCardWrapper={true}
            textAlign="text-center"
          />
        </div>
      </div>
      <div className='mt-4'>
        <p className='text-muted text-center reporting-description-small'>
          Performance metrics are calculated from feature management activity data
        </p>
      </div>
    </div>
  )

  const renderHealthContent = () => (
    <div>
      <SectionHeader
        title="Health Check"
        description="Feature health and optimization recommendations"
      />
      <div className='row g-3'>
        <div className='col-md-6'>
          <MetricCard
            title="Unused Features"
            value={healthMetrics.unusedFeatures}
            variant="complex"
            description="Features not used in 30+ days"
            progressBar={{
              width: `${Math.min(healthMetrics.unusedFeatures * 2, 100)}%`, // Scale for progress bar
              color: 'var(--bs-primary)'
            }}
            showCardWrapper={true}
          >
            <p className='text-muted mb-0 text-center reporting-description-small'>
              Consider archiving or removing these features to reduce complexity
            </p>
          </MetricCard>
        </div>
        <div className='col-md-6'>
          <MetricCard
            title="Stale Features"
            value={healthMetrics.staleFeatures}
            variant="complex"
            description="Features not updated in 90+ days"
            progressBar={{
              width: `${Math.min(healthMetrics.staleFeatures * 3, 100)}%`, // Scale for progress bar
              color: 'var(--bs-primary)'
            }}
            showCardWrapper={true}
          >
            <p className='text-muted mb-0 text-center reporting-description-small'>
              These features may need attention or updates
            </p>
          </MetricCard>
        </div>
      </div>
      <div className='mt-4'>
        <MetricCard
          showCardWrapper={true}
          cardVariant="info"
        >
          <h6 className='mb-3 reporting-subtitle'>
            <Icon name='info' className='me-2' />
            Recommendations
          </h6>
          <ul className='mb-0 text-muted reporting-description'>
            <li>Review unused features and consider archiving them</li>
            <li>Update stale features to ensure they're still relevant</li>
            <li>Consider consolidating similar features</li>
            <li>Set up automated alerts for feature health</li>
          </ul>
        </MetricCard>
      </div>
    </div>
  )

  return (
    <div className={className}>
      <Tabs
        value={activeTab}
        onChange={setActiveTab}
        className='mb-4'
        theme='tab'
      >
        <TabItem tabLabel='Overview' tabLabelString='overview'>
          <MetricsOverview
            context={context}
            contextId={contextId}
            filters={filters}
          />
        </TabItem>
        
        <TabItem tabLabel='Activity' tabLabelString='activity'>
          <ActivityMetrics
            context={context}
            contextId={contextId}
            filters={filters}
          />
        </TabItem>
        
        <TabItem tabLabel='Performance' tabLabelString='performance'>
          {renderPerformanceContent()}
        </TabItem>
        
        <TabItem tabLabel='Health' tabLabelString='health'>
          {renderHealthContent()}
        </TabItem>
      </Tabs>
    </div>
  )
}

export default TabbedReportingDashboard
