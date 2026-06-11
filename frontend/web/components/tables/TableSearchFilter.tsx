import React, { FC, useState } from 'react'
import SearchInput from 'components/base/forms/SearchInput'
import Utils from 'common/utils/utils'
import useDebounce from 'common/useDebounce'

type TableFilterType = {
  exact?: boolean
  value: string | null | undefined
  onChange: (v: string) => void
}

const TableSearchFilter: FC<TableFilterType> = ({ onChange, value }) => {
  const [localValue, setLocalValue] = useState(
    (value || '').replace(/^"+|"+$/g, ''),
  )
  const debouncedOnChange = useDebounce((v: string) => onChange(v), 100)

  return (
    <SearchInput
      onChange={(e) => {
        const v = Utils.safeParseEventValue(e)
        setLocalValue(v)
        debouncedOnChange(v)
      }}
      value={localValue}
      className='me-3'
      size='xSmall'
      placeholder='Search'
    />
  )
}

export default TableSearchFilter
