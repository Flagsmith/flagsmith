import React, { FC, ReactNode, useMemo, useState } from 'react'
import InlineModal from 'components/InlineModal'
import { IonIcon } from '@ionic/react'
import { caretDown, search } from 'ionicons/icons'
import classNames from 'classnames'
import TableFilterItem from './TableFilterItem'
import Input from 'components/base/forms/Input'
import Utils from 'common/utils/utils'

type TableFilterType = {
  title: ReactNode
  dropdownTitle?: ReactNode | string
  className?: string
  size?: 'sm' | 'lg'
  isLoading?: boolean
  options: { label: string; value: string | number; subtitle?: string }[]
  onChange: (value: string | string[]) => void | Promise<void>
  value: (string | number) | (string | number)[]
  multiple?: boolean
  showSearch?: boolean
}

const TableFilter: FC<TableFilterType> = ({
  className,
  isLoading,
  multiple,
  onChange,
  options,
  showSearch,
  size = 'sm',
  title,
  value,
}) => {
  const [filter, setFilter] = useState('')

  const [open, setOpen] = useState(false)
  const toggle = function () {
    if (!open) {
      setOpen(true)
    }
  }

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
      <Row
        onClick={toggle}
        className={classNames('cursor-pointer user-select-none', className)}
      >
        <span>{title} </span>
        <IonIcon
          style={{
            fontSize: 11,
            marginLeft: 2,
            marginTop: 4,
          }}
          icon={caretDown}
        />
      </Row>
      {open && (
        <InlineModal
          hideClose
          title={null}
          isOpen={open}
          onClose={() => {
            setTimeout(() => {
              setOpen(false)
            }, 10)
          }}
          containerClassName='px-0'
          className={`inline-modal table-filter inline-modal--${size} right`}
        >
          {!!showSearch && (
            <div className='px-2 mt-2 mb-2'>
              <Input
                autoFocus
                onChange={(e: InputEvent) => {
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
                    setOpen(false)
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
        </InlineModal>
      )}
    </div>
  )
}

export default TableFilter
