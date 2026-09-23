import { FC } from 'react'
import { BillingPeriod, PeriodOption } from 'common/types/requests'
import ProjectFilter from 'components/ProjectFilter'
import { PeriodSelection } from 'components/pages/usage/utils'
import './UsageFilters.scss'

export type UsageFiltersProps = {
  organisationId: number
  periods: PeriodOption[]
  period: BillingPeriod
  onChangePeriod: (period: PeriodSelection) => void
  projectId: string | undefined
  onChangeProject: (id: string, name: string) => void
}

const UsageFilters: FC<UsageFiltersProps> = ({
  onChangePeriod,
  onChangeProject,
  organisationId,
  period,
  periods,
  projectId,
}) => (
  <Row className='gap-2'>
    <div className='usage-filters__field'>
      <Select
        aria-label='Period'
        inputId='usage-period'
        onChange={(option: PeriodOption) => onChangePeriod(option.value)}
        value={periods.find((option) => option.value === period)}
        options={periods}
      />
    </div>
    <div className='usage-filters__field'>
      <ProjectFilter
        aria-label='Project'
        inputId='usage-project'
        showAll
        organisationId={organisationId}
        onChange={onChangeProject}
        value={projectId}
      />
    </div>
  </Row>
)

export default UsageFilters
