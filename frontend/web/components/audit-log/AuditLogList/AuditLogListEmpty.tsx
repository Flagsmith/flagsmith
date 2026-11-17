import { FC } from 'react'
import Button from 'components/base/forms/Button'
import EmptyState from 'components/EmptyState'

type AuditLogListEmptyProps = {
  hasFilters: boolean
  onClearFilters: () => void
}

const AuditLogListEmpty: FC<AuditLogListEmptyProps> = ({
  hasFilters,
  onClearFilters,
}) =>
  hasFilters ? (
    <EmptyState
      icon='search'
      title='No changes match these filters'
      description='Try a shorter search.'
      action={
        <Button theme='outline' size='small' onClick={onClearFilters}>
          Clear filters
        </Button>
      }
    />
  ) : (
    <EmptyState
      icon='list'
      title='No activity yet'
      description='Changes to projects, flags, segments and members will show up here.'
    />
  )

export default AuditLogListEmpty
