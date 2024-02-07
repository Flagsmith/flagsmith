import React, { FC, useEffect, useState } from 'react'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { useGetConversionEventsQuery } from 'common/services/useConversionEvent'
import useSearchThrottle from 'common/useSearchThrottle'
import { ConversionEvent } from 'common/types/responses'

type ConversionEventSelectType = {
  onChange: (v: number) => void
}

const ConversionEventSelect: FC<ConversionEventSelectType> = ({ onChange }) => {
  const { search, searchInput, setSearchInput } = useSearchThrottle('')
  const { data } = useGetConversionEventsQuery({ q: `${search}` })
  const [selected, setSelected] = useState<ConversionEvent | null>(null)

  return (
    <div>
      <Select
        value={
          selected
            ? { label: selected.name, value: selected.id }
            : {
                label: 'Select an Event',
                value: '',
              }
        }
        inputValue={searchInput}
        onInputChange={setSearchInput}
        options={data?.results?.map((result) => ({
          ...result,
          label: result.name,
          value: result.id,
        }))}
        onChange={(value: ConversionEvent) => {
          setSelected(value)
          onChange(value.id)
        }}
      />
    </div>
  )
}

export default ConversionEventSelect
