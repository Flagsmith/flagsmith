import React, { FC } from 'react'
import ProjectFilter from 'components/ProjectFilter'
import { billingPeriods, freePeriods, Req } from 'common/types/requests'

interface UsageChartFiltersProps {
  organisationId: number
  project: string | undefined
  setProject: (project: string | undefined) => void
  billingPeriod: Req['getOrganisationUsage']['billing_period']
  setBillingPeriod: (
    period: Req['getOrganisationUsage']['billing_period'],
  ) => void
  isOnFreePlanPeriods: boolean
}

const UsageChartFilters: FC<UsageChartFiltersProps> = ({
  billingPeriod,
  isOnFreePlanPeriods,
  organisationId,
  project,
  setBillingPeriod,
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
    </div>
  )
}

export default UsageChartFilters
