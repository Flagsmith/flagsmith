import React, { FC } from 'react'
import TableFilterItem from './TableFilterItem'
import TableFilter from './TableFilter'
import { SortOrder } from 'common/types/requests'

type SortType = {
  value: string
  label: string
}
export type SortValue = {
  sortBy: string
  label: string
  sortOrder: SortOrder
}
type TableFilterType = {
  options: SortType[]
  isLoading: boolean
  value: SortValue
  onChange: (v: SortValue) => void
}

const oppositeOrder = (order: SortOrder) =>
  order === SortOrder.ASC ? SortOrder.DESC : SortOrder.ASC

const TableSortFilter: FC<TableFilterType> = ({
  isLoading,
  onChange,
  options,
  value: _value,
}) => {
  const value = _value || {
    label: options[0].label,
    sortBy: options[0].value,
    sortOrder: SortOrder.ASC,
  }
  return (
    <div className={isLoading ? 'disabled' : ''}>
      <TableFilter title={'Sort'}>
        {options.map((sortOption, i) => {
          const isActive = sortOption?.value === value?.sortBy
          return (
            <TableFilterItem
              key={i}
              title={sortOption.label}
              isActive={isActive}
              sortOrder={value.sortOrder}
              onClick={() => {
                if (isLoading) return
                onChange({
                  label: sortOption.label,
                  sortBy: sortOption.value,
                  sortOrder: isActive
                    ? oppositeOrder(value.sortOrder)
                    : SortOrder.ASC,
                })
              }}
            />
          )
        })}
      </TableFilter>
    </div>
  )
}

export default TableSortFilter
