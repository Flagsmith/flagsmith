import React, { FC, useMemo } from 'react'
import TableFilterOptions from './TableFilterOptions'
import { sortBy } from 'lodash'
import { useGetGroupSummariesQuery } from 'common/services/useGroupSummary'

type TableFilterType = {
  value: number[]
  onChange: (value: TableFilterType['value']) => void
  className?: string
  isLoading?: boolean
  orgId: string | undefined
}

const TableGroupsFilter: FC<TableFilterType> = ({
  className,
  isLoading,
  onChange,
  orgId,
  value,
}) => {
  const { data } = useGetGroupSummariesQuery(
    { orgId: orgId || '' },
    { skip: !orgId },
  )
  const groups = useMemo(() => {
    return sortBy(
      (data || []).map((item) => ({
        label: `${item.name}`,
        value: item.id,
      })),
      'label',
    )
  }, [data])

  return (
    <TableFilterOptions
      className={className}
      title={
        <Row>
          Groups{' '}
          {!!value?.length && (
            <span className='mx-1 unread d-inline'>{value.length}</span>
          )}
        </Row>
      }
      isLoading={isLoading}
      multiple
      showSearch
      options={groups}
      onChange={onChange as any}
      value={value}
    />
  )
}

export default TableGroupsFilter
