import React, { FC, useState } from 'react'
import TableFilter from './TableFilter'
import Icon from 'components/Icon'

export type SortType = {
  value: string
  label: string
  sortOrder: 'asc' | 'desc' | null
}
export type SortValue = {
  sortBy: string
  label: string
  sortOrder: 'asc' | 'desc' | null
}
type TableFilterType = {
  options: SortType[]
  value: SortValue
  onChange: (v: SortValue) => void
}

const TableSortFilter: FC<TableFilterType> = ({
  onChange,
  options,
  value: _value,
}) => {
  const [open, setOpen] = useState(false)

  const value = _value || {
    label: options[0].label,
    sortBy: options[0].value,
    sortOrder: 'asc',
  }
  return (
    <>
      <TableFilter title={'Sort'}>
        {options.map((sortOption, i) => {
          const isActive = sortOption?.value === value?.sortBy
          return (
            <a
              key={i}
              className='popover-bt__list-item'
              href='#'
              onClick={() => {
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
                {isActive && (
                  <div>
                    <Icon
                      className='text-body'
                      name={
                        value?.sortOrder === 'asc'
                          ? 'chevron-up'
                          : 'chevron-down'
                      }
                    />
                  </div>
                )}
              </Row>
            </a>
          )
        })}
      </TableFilter>
    </>
  )
}

export default TableSortFilter
