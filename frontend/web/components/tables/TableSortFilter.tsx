import React, { FC } from 'react'
import TableFilter from './TableFilter'
import Icon from 'components/Icon'
import classNames from 'classnames'

export type SortType = {
  value: string
  label: string
}
export type SortValue = {
  sortBy: string
  label: string
  sortOrder: 'asc' | 'desc' | null
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
    sortOrder: 'asc',
  }
  return (
    <div className={isLoading ? 'disabled' : ''}>
      <TableFilter hideTitle title={'Sort'}>
        {options.map((sortOption, i) => {
          const isActive = sortOption?.value === value?.sortBy
          return (
            <a
              key={i}
              className='popover-bt__list-item'
              href='#'
              onClick={(e) => {
                e.preventDefault()
                if (isLoading) return
                onChange({
                  label: sortOption.label,
                  sortBy: sortOption.value,
                  sortOrder: isActive
                    ? value.sortOrder === 'asc'
                      ? 'desc'
                      : 'asc'
                    : 'asc',
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
                      value?.sortOrder === 'asc' ? 'chevron-up' : 'chevron-down'
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
