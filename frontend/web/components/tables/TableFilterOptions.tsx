import React, { FC, ReactNode, useMemo, useState } from 'react'
import classNames from 'classnames'
import TableFilter from './TableFilter'
import TableFilterItem from './TableFilterItem'
import Input from 'components/base/forms/Input'
import Utils from 'common/utils/utils'

type TableFilterOptionsType = {
  title: ReactNode
  label?: string
  dropdownTitle?: ReactNode | string
  className?: string
  isLoading?: boolean
  options: { label: string; value: string | number; subtitle?: string }[]
  onChange: (value: string | string[]) => void | Promise<void>
  value: (string | number) | (string | number)[]
  multiple?: boolean
  showSearch?: boolean
}

const TableFilterOptions: FC<TableFilterOptionsType> = ({
  className,
  isLoading,
  label,
  multiple,
  onChange,
  options,
  showSearch,
  title,
  value,
}) => {
  const [filter, setFilter] = useState('')

  const filteredOptions = useMemo(() => {
    const lowerSearch = filter?.toLowerCase()
    return filter
      ? options.filter((v) => {
          return v.label.toLowerCase().includes(lowerSearch)
        })
      : options
  }, [options, filter])

  return (
    <div className={isLoading ? 'disabled' : ''}>
      <TableFilter
        title={title}
        label={label}
        hideTitle
        className={classNames('user-select-none', className)}
      >
        {(close) => (
          <>
            {!!showSearch && (
              <div className='px-3 my-2'>
                <Input
                  autoFocus
                  onChange={(e) => {
                    setFilter(Utils.safeParseEventValue(e))
                  }}
                  className='full-width'
                  value={filter}
                  type='text'
                  size='xSmall'
                  placeholder='Search'
                  search
                />
                {!filteredOptions?.length && (
                  <div className='text-center py-2'>No results</div>
                )}
              </div>
            )}
            <div className='table-filter-list'>
              {filteredOptions.map((v) => (
                <TableFilterItem
                  key={v.value}
                  title={v.label}
                  subtitle={v.subtitle}
                  onClick={() => {
                    if (!multiple) {
                      close()
                    }
                    if (multiple) {
                      if ((value || []).includes(v.value)) {
                        onChange(
                          ((value as string[]) || []).filter(
                            (item) => item !== v.value,
                          ),
                        )
                      } else {
                        onChange(((value as string[]) || []).concat([v.value]))
                      }
                    } else {
                      onChange(v.value)
                    }
                  }}
                  isActive={
                    multiple ? value?.includes(v.value) : value === v.value
                  }
                />
              ))}
            </div>
          </>
        )}
      </TableFilter>
    </div>
  )
}

export default TableFilterOptions
