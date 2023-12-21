import React, { FC, useCallback, useEffect, useState } from 'react'
import TableFilter from './TableFilter'
import Input from 'components/base/forms/Input'
import Utils from 'common/utils/utils'
import { exact } from 'prop-types'
import useThrottle from 'common/useThrottle'

type TableFilterType = {
  exact?: boolean
  value: string | null | undefined
  onChange: (v: string) => void
}

const TableSearchFilter: FC<TableFilterType> = ({ exact, onChange, value }) => {
  const [localValue, setLocalValue] = useState(value)
  const searchItems = useThrottle(
    useCallback((search) => {
      if (value !== search) {
        onChange(search)
      }
    }, []),
    100,
  )
  useEffect(() => {
    searchItems(localValue)
  }, [localValue])
  return (
    <>
      <Input
        onChange={(e: InputEvent) => {
          const v = Utils.safeParseEventValue(e)
          setLocalValue(v)
        }}
        value={localValue?.replace(/^"+|"+$/g, '')}
        type='text'
        className='me-3'
        size='xSmall'
        placeholder='Search'
        search
      />
    </>
  )
}

export default TableSearchFilter
