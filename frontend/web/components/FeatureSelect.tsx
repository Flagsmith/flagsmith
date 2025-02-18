import React, { useEffect, useState } from 'react'
import sortBy from 'lodash/sortBy'
import { ProjectFlag } from 'common/types/responses'
import { useGetProjectFlagsQuery } from 'common/services/useProjectFlag'

type OptionType = {
  flag: ProjectFlag
  label: string
  value: number
}

type FeatureSelectProps = {
  autoSelectFirst?: boolean
  disabled?: boolean
  ignore?: number[]
  onChange: (value: number, flag: ProjectFlag) => void
  onlyInclude?: number
  placeholder?: string
  projectId: string
  value?: number | string
}

const FeatureSelect = ({
  autoSelectFirst,
  disabled,
  ignore = [],
  onChange,
  onlyInclude,
  placeholder,
  projectId,
  value,
}: FeatureSelectProps): JSX.Element => {
  const [search, setSearch] = useState('')
  const { data, isLoading } = useGetProjectFlagsQuery(
    { project: projectId, search },
    { skip: !projectId },
  )

  useEffect(() => {
    if (data?.results?.length && autoSelectFirst && !value) {
      const flag = sortBy(data?.results, 'name')[0]
      onChange(flag.id, flag)
    }
  }, [data, autoSelectFirst, value])

  if (!data || isLoading) {
    return (
      <div className='text-center'>
        {/* Use your Loader component or any loading indicator */}
        <Loader />
      </div>
    )
  }

  const options: OptionType[] = sortBy(
    (data.results || [])
      .map((feature) => ({
        flag: feature,
        label: feature.name,
        value: feature.id,
      }))
      .filter((opt) => !ignore.includes(opt.value))
      .filter((opt) => {
        if (onlyInclude) {
          return opt.value === onlyInclude
        }
        return true
      }),
    (o) => o.label,
  )

  return (
    <Select
      value={value ? options.find((o) => `${o.value}` === `${value}`) : null}
      isDisabled={disabled}
      onInputChange={(inputValue: string) => {
        setSearch(inputValue)
      }}
      placeholder={placeholder}
      onChange={(selected: OptionType) => {
        if (!selected) return
        const option = selected as OptionType
        onChange(option.value, option.flag)
      }}
      options={options}
    />
  )
}

export default FeatureSelect
