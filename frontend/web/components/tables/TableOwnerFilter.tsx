import React, { FC, useMemo } from 'react'
import { User } from 'common/types/responses'
import OrganisationStore from 'common/stores/organisation-store'
import TableFilterOptions from './TableFilterOptions'

type TableFilterType = {
  value: number[]
  onChange: (value: TableFilterType['value']) => void
  className?: string
  isLoading?: boolean
}

const TableOwnerFilter: FC<TableFilterType> = ({
  className,
  isLoading,
  onChange,
  value,
}) => {
  const orgUsers = OrganisationStore.model && OrganisationStore.model.users
  const users = useMemo(() => {
    return (orgUsers || []).map((item: User) => ({
      label: `${item.first_name} ${item.last_name}`,
      subtitle: item.email,
      value: item.id,
    }))
  }, [orgUsers])

  return (
    <TableFilterOptions
      size='lg'
      className={className}
      isLoading={isLoading}
      title={
        <Row>
          Users{' '}
          {!!value?.length && (
            <span className='mx-1 unread d-inline'>{value.length}</span>
          )}
        </Row>
      }
      multiple
      showSearch
      options={users}
      onChange={onChange as any}
      value={value}
    />
  )
}

export default TableOwnerFilter
