import React, { FC } from 'react'
import ProjectFilter from 'components/ProjectFilter'
import EnvironmentFilter from 'components/EnvironmentFilter'
import { billingPeriods, freePeriods, Req } from 'common/types/requests'

export interface UsageChartFiltersProps {
  organisationId: number
  project: string | undefined
  setProject: (project: string | undefined) => void
  environment: string | undefined
  setEnvironment: (environment: string | undefined) => void
  billingPeriod: Req['getOrganisationUsage']['billing_period']
  setBillingPeriod: (
    period: Req['getOrganisationUsage']['billing_period'],
  ) => void
  isOnFreePlanPeriods: boolean
}

const UsageChartFilters: FC<UsageChartFiltersProps> = ({
  billingPeriod,
  environment,
  isOnFreePlanPeriods,
  organisationId,
  project,
  setBillingPeriod,
  setEnvironment,
  setProject,
}) => {
  return (
    <div className='row'>
      <div className='col-md-4'>
        <label>Period</label>
        <Select
          onChange={(v: any) => setBillingPeriod(v.value)}
          value={billingPeriods.find((v) => v.value === billingPeriod)}
          options={isOnFreePlanPeriods ? freePeriods : billingPeriods}
        />
      </div>
      <div className='col-md-4 mb-5'>
        <label>Project</label>
        <ProjectFilter
          showAll
          organisationId={organisationId}
          onChange={setProject}
          value={project}
        />
      </div>
      {project && (
        <div className='col-md-4'>
          <label>Environment</label>
          <EnvironmentFilter
            showAll
            projectId={project}
            onChange={setEnvironment}
            value={environment}
          />
        </div>
      )}
    </div>
  )
}

export default UsageChartFilters
