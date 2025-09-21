import React, { FC } from 'react'
import { useParams, Link } from 'react-router-dom'
import PageTitle from 'components/PageTitle'
import AccountStore from 'common/stores/account-store'
import { ProjectEnvironmentFilters, TabbedReportingDashboard } from '../components'
import { useReportingFilters } from '../hooks'

const ProjectReportingPage: FC = () => {
  const { projectId } = useParams<{ projectId: string }>()
  
  // Use business logic hooks
  const { filters, setFilters } = useReportingFilters('project', projectId || '')
  
  // Admin permission check
  const isAdmin = AccountStore.isAdmin()
  
  // Organization reporting URL - simplified
  const organizationReportingUrl = '/organisation/1/reporting' // TODO: Replace with actual organization ID

  return (
    <div className='app-container container'>
      <PageTitle title='Project Insights'>
        Track your feature management success for this project.
      </PageTitle>
      <ProjectEnvironmentFilters
        context="project"
        contextId={projectId || ''}
        filters={filters}
        onFiltersChange={setFilters}
      />

      <TabbedReportingDashboard
        context="project"
        contextId={projectId || ''}
        filters={filters}
      />
      {isAdmin && (
        <div className='mt-5 pt-4 border-top'>
          <div className='d-flex justify-content-between align-items-center'>
            <div>
              <h5 className='mb-1 reporting-title'>
                View Organization Context
              </h5>
              <p className='text-muted mb-0 reporting-section-description'>
                See how this project compares to your organization-wide program
              </p>
            </div>
            <Link 
              to={organizationReportingUrl}
              className='btn btn-primary'
            >
              View Organization Dashboard →
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}

export default ProjectReportingPage
