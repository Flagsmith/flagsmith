import React, { FC } from 'react'
import TableFilter from './TableFilter'
import Icon from 'components/Icon'
import classNames from 'classnames'
import { SortOrder } from 'common/types/requests'

export type SortType = {
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
      <TableFilter hideTitle title={'Sort'}>
        {options.map((sortOption, i) => {
          const isActive = sortOption?.value === value?.sortBy
          return (
            <a
              key={i}
              className='table-filter-item'
              href='#'
              onClick={(e) => {
                e.preventDefault()
                if (isLoading) return
                onChange({
                  label: sortOption.label,
                  sortBy: sortOption.value,
                  sortOrder: isActive
                    ? value.sortOrder === SortOrder.ASC
                      ? SortOrder.DESC
                      : SortOrder.ASC
                    : SortOrder.ASC,
                })
              }}
            >
              <Row space className='px-3 py-2'>
                <div>{sortOption.label}</div>
                <div>
                  <Icon
                    className={classNames('text-body', {
                      'opacity-0': !isActive,
                    })}
                    name={
                      value?.sortOrder === SortOrder.ASC
                        ? 'chevron-up'
                        : 'chevron-down'
                    }
                  />
                </div>
              </Row>
            </a>
          )
        })}
      </TableFilter>
    </div>
  )
}

export default TableSortFilter
