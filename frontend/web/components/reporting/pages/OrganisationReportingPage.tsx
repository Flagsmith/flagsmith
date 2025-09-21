import React, { FC } from 'react'
import { useParams } from 'react-router-dom'
import PageTitle from 'components/PageTitle'
import { ProjectEnvironmentFilters, TabbedReportingDashboard } from '../components'
import { useReportingFilters } from '../hooks'

const OrganisationReportingPage: FC = () => {
  const { organisationId } = useParams<{ organisationId: string }>()
  
  const { filters, setFilters } = useReportingFilters('organisation', organisationId || '')

  return (
    <div className='app-container container'>
      <PageTitle title='Feature Management Reporting'>
        Track your organization's feature management program success across all projects.
      </PageTitle>
      
      <ProjectEnvironmentFilters
        context="organisation"
        contextId={organisationId || ''}
        filters={filters}
        onFiltersChange={setFilters}
      />

      <TabbedReportingDashboard
        context="organisation"
        contextId={organisationId || ''}
        filters={filters}
      />
    </div>
  )
}

export default OrganisationReportingPage
