import React, { FC, useEffect, useMemo, useRef, useState } from 'react'
import TableFilter from './TableFilter'
import Utils from 'common/utils/utils'
import InputGroup from 'components/base/forms/InputGroup'
import useDebouncedSearch from 'common/useDebouncedSearch'

type TableFilterType = {
  value: {
    enabled: boolean | null
    valueSearch: string | null
  }
  isLoading?: boolean
  onChange: (value: TableFilterType['value']) => void
  className?: string
}

const enabledOptions = [
  {
    label: 'Any',
    value: null,
  },
  {
    label: 'Enabled',
    value: true,
  },
  {
    label: 'Disabled',
    value: false,
  },
]
const TableTagFilter: FC<TableFilterType> = ({
  className,
  isLoading,
  onChange,
  value,
}) => {
  const { searchInput, setSearchInput } = useDebouncedSearch('')

  return (
    <div className={isLoading ? 'disabled' : ''}>
      <TableFilter
        className={className}
        hideTitle
        title={
          <Row>
            Value{' '}
            {(value.enabled !== null || !!value.valueSearch) && (
              <span className='mx-1 unread d-inline'>{1}</span>
            )}
          </Row>
        }
      >
        <div className='inline-modal__list d-flex flex-column mx-0 py-0'>
          <div className='px-2 mt-2'>
            <InputGroup
              title='Enabled State'
              className='mt-2'
              component={
                <Select
                  size='select-xxsm'
                  styles={{
                    control: (base) => ({
                      ...base,
                      height: 18,
                    }),
                  }}
                  onChange={(e: (typeof enabledOptions)[number]) => {
                    onChange({
                      enabled: e.value,
                      valueSearch: value.valueSearch,
                    })
                  }}
                  value={enabledOptions.find((v) => v.value === value.enabled)}
                  options={enabledOptions}
                />
              }
            />
            <InputGroup
              title='Feature Value'
              autoFocus
              onChange={(e: InputEvent) => {
                setSearchInput(Utils.safeParseEventValue(e))
              }}
              tooltip='This will filter your features based on the remote configuration value you define.'
              inputProps={{ style: { height: 60 } }}
              value={searchInput}
              textarea
              rows={2}
              className='full-width mt-2'
              type='text'
              size='xSmall'
              placeholder='Enter a feature value'
              search
            />
          </div>
        </div>
      </TableFilter>
    </div>
  )
}

export default TableTagFilter
