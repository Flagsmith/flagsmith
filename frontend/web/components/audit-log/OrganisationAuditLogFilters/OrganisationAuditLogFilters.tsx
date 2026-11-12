import { ChangeEvent, FC } from 'react'
import Input from 'components/base/forms/Input'
import Button from 'components/base/forms/Button'
import {
  AuditLogFilters,
  showsClearAll,
} from 'components/audit-log/auditLogFilters'
import { AuditLogScopeFilter } from 'components/audit-log/auditLogScopeFilter'
import { ScopeCardEnvironment, ScopeCardProject, ScopeList } from './ScopeCard'
import ScopeFilter from './ScopeFilter'
import './OrganisationAuditLogFilters.scss'

type OrganisationAuditLogFiltersProps = {
  filters: AuditLogFilters
  searchInput: string
  projects: ScopeList<ScopeCardProject>
  environments: ScopeList<ScopeCardEnvironment>
  setSearchInput: (value: string) => void
  setScope: (scope: AuditLogScopeFilter) => void
  onClearAll: () => void
}

const OrganisationAuditLogFilters: FC<OrganisationAuditLogFiltersProps> = ({
  environments,
  filters,
  onClearAll,
  projects,
  searchInput,
  setScope,
  setSearchInput,
}) => {
  return (
    <div className='d-flex flex-wrap align-items-center gap-2'>
      <div className='audit-log-filters__search flex-grow-1 flex-sm-grow-0'>
        <Input
          type='text'
          search
          size='xSmall'
          className='w-100'
          value={searchInput}
          placeholder='Search changes'
          aria-label='Search changes'
          onChange={(e: ChangeEvent<HTMLInputElement>) =>
            setSearchInput(e.target.value)
          }
        />
      </div>
      <ScopeFilter
        scope={filters.scope}
        projects={projects}
        environments={environments}
        onChange={setScope}
      />
      {showsClearAll(filters) && (
        <Button theme='text' size='small' onClick={onClearAll}>
          Clear all
        </Button>
      )}
    </div>
  )
}

export default OrganisationAuditLogFilters
