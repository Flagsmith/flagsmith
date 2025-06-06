import React, { FC, useState } from 'react'
import { useGetConversionEventsQuery } from 'common/services/useConversionEvent'
import useSearchThrottle from 'common/useSearchThrottle'
import { ConversionEvent } from 'common/types/responses'
import ProjectStore from 'common/stores/project-store'

type ConversionEventSelectType = {
  onChange: (v: number) => void
  environmentId: string
}

const ConversionEventSelect: FC<ConversionEventSelectType> = ({
  environmentId,
  onChange,
}) => {
  const { search, searchInput, setSearchInput } = useSearchThrottle('')
  const { data } = useGetConversionEventsQuery({
    environment_id: ProjectStore.getEnvironmentIdFromKey(environmentId),
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
