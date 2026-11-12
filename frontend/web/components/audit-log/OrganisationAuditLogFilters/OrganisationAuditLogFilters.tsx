import { ChangeEvent, FC } from 'react'
import Input from 'components/base/forms/Input'
import Button from 'components/base/forms/Button'
import {
  AuditLogFilters,
  hasActiveAuditLogFilters,
} from 'components/audit-log/auditLogFilters'
import './OrganisationAuditLogFilters.scss'

type OrganisationAuditLogFiltersProps = {
  filters: AuditLogFilters
  searchInput: string
  setSearchInput: (value: string) => void
  onClearAll: () => void
}

const OrganisationAuditLogFilters: FC<OrganisationAuditLogFiltersProps> = ({
  filters,
  onClearAll,
  searchInput,
  setSearchInput,
}) => (
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
    {hasActiveAuditLogFilters(filters) && (
      <Button theme='text' size='small' onClick={onClearAll}>
        Clear all
      </Button>
    )}
  </div>
)

export default OrganisationAuditLogFilters
