import React, { FC, useState } from 'react'
import { useGetConversionEventsQuery } from 'common/services/useConversionEvent'
import useDebouncedSearch from 'common/useDebouncedSearch'
import { ConversionEvent } from 'common/types/responses'
import ProjectStore from 'common/stores/project-store'

type ConversionEventSelectType = {
  onChange: (v: number) => void
  environmentKey: string
}

const ConversionEventSelect: FC<ConversionEventSelectType> = ({
  environmentKey,
  onChange,
}) => {
  const { search, searchInput, setSearchInput } = useDebouncedSearch('')
  const { data } = useGetConversionEventsQuery({
    environment_id: ProjectStore.getEnvironmentIdFromKey(environmentKey),
    q: `${search}`,
  })
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
