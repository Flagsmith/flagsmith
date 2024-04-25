import React from 'react'
import { ProjectFlag } from 'common/types/responses'
import useSearchThrottle from 'common/useSearchThrottle'
import { useGetFeaturesQuery } from 'common/services/useFeature'

interface Props {
  projectId: string | undefined
  value?: number
  disabled?: boolean
  onChange: (value: number, flag: ProjectFlag) => void
  ignore?: number[]
  onlyInclude?: number
  placeholder?: string
}

const FlagSelect: React.FC<Props> = ({
  disabled,
  ignore = [],
  onChange,
  onlyInclude,
  placeholder,
  projectId,
  value,
}) => {
  const { search, setSearchInput } = useSearchThrottle()

  const { data, isLoading } = useGetFeaturesQuery(
    { page: 1, page_size: 3, project_id: `${projectId}`, search },
    { skip: !projectId },
  )

  if (!data || isLoading) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }

  const options = data?.results
    .map((v) => ({ flag: v, label: v.name, value: v.id }))
    .filter((v) => !ignore.includes(v.value))
    .filter((v) => {
      if (onlyInclude && v.value !== onlyInclude) {
        return false
      }
      return true
    })
    .sort((a, b) => a.label.localeCompare(b.label))

  return (
    <Select
      value={value ? options.find((v) => v.value === value) : null}
      isDisabled={disabled}
      onInputChange={setSearchInput}
      placeholder={placeholder || 'Select a feature...'}
      onChange={(v: { flag: ProjectFlag; value: number }) =>
        onChange(v.value, v.flag)
      }
      options={options}
    />
  )
}

export default FlagSelect
