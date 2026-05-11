import React, { FC, useEffect } from 'react'
import flagsmith from '@flagsmith/flagsmith'
import { useFlags } from '@flagsmith/flagsmith/react'
import TableFilter from './TableFilter'
import Utils from 'common/utils/utils'
import InputGroup from 'components/base/forms/InputGroup'
import Checkbox from 'components/base/forms/Checkbox'
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
  const { search, searchInput, setSearchInput } = useDebouncedSearch(
    value?.valueSearch || '',
  )
  const flags = useFlags(['display_feature_null_values'])
  const isNullDisplayEnabled = !!flags.display_feature_null_values?.enabled
  useEffect(() => {
    if ((search || '') !== (value.valueSearch || '')) {
      onChange({
        enabled: value.enabled,
        valueSearch: search,
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, value])
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
        <div
          className='inline-modal__list d-flex flex-column mx-0'
          style={{ maxHeight: 'none' }}
        >
          <div className='p-3' style={{ minWidth: 320 }}>
            <InputGroup
              title='Enabled State'
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
            <div className='mt-3'>
              <Checkbox
                label='Show null and empty values'
                checked={isNullDisplayEnabled}
                onChange={(checked) => {
                  flagsmith.setTrait(
                    'opt_in_null_feature_values',
                    checked ? true : null,
                  )
                }}
              />
            </div>
          </div>
        </div>
      </TableFilter>
    </div>
  )
}

export default TableTagFilter
