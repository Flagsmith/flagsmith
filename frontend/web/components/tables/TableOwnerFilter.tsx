import React, { FC, useEffect, useMemo, useRef, useState } from 'react'
import TableFilter from './TableFilter'
import Input from 'components/base/forms/Input'
import Utils from 'common/utils/utils'
import { useGetTagsQuery } from 'common/services/useTag'
import Tag from 'components/tags/Tag'
import TableFilterItem from './TableFilterItem'
import Constants from 'common/constants'
import { TagStrategy } from 'common/types/responses'
import { AsyncStorage } from 'polyfill-react-native'
import InputGroup from 'components/base/forms/InputGroup'
import useSearchThrottle from 'common/useSearchThrottle'

type TableFilterType = {
  value: {
    owners: number[]
    groupOwners: string | null
  }
  onChange: (value: TableFilterType['value']) => void
  className?: string
  useLocalStorage?: boolean
  projectId: string
}

const TableTagFilter: FC<TableFilterType> = ({
  className,
  onChange,
  projectId,
  useLocalStorage,
  value,
}) => {
  const checkedLocalStorage = useRef(false)

  useEffect(() => {
    if (checkedLocalStorage.current && useLocalStorage) {
      AsyncStorage.setItem(`${projectId}-value`, JSON.stringify(value))
    }
  }, [value, projectId, useLocalStorage])
  useEffect(() => {
    const checkLocalStorage = async function () {
      if (useLocalStorage && !checkedLocalStorage.current) {
        checkedLocalStorage.current = true
        const storedValue = await AsyncStorage.getItem(`${projectId}-value`)
        if (storedValue) {
          try {
            const storedValueObject = JSON.parse(storedValue)
            onChange(storedValueObject)
          } catch (e) {}
        }
      }
    }
    checkLocalStorage()
  }, [useLocalStorage, projectId])
  return (
    <div>
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
                      '&:hover': { borderColor: '$bt-brand-secondary' },
                      border: '1px solid $bt-brand-secondary',
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
