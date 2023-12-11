import React, { FC, useState } from 'react'
import TableFilter from './TableFilter'
import Input from 'components/base/forms/Input'
import Utils from 'common/utils/utils'
import { exact } from 'prop-types'

type TableFilterType = {
  exact?: boolean
  value: string | null | undefined
  onChange: (v: string) => void
}

const TableSearchFilter: FC<TableFilterType> = ({ exact, onChange, value }) => {
  return (
    <>
      <Input
        onChange={(e: InputEvent) => {
          const v = Utils.safeParseEventValue(e)
          onChange(exact ? `"${v}"` : v)
        }}
        value={value?.replace(/^"+|"+$/g, '')}
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
