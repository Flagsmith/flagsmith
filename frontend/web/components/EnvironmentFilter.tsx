import { FC, useMemo } from 'react'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'

export type EnvironmentFilterType = {
  projectId: string
  value?: string
  onChange: (value: string) => void
  showAll?: boolean
  disabled?: boolean
}

const EnvironmentFilter: FC<EnvironmentFilterType> = ({
  onChange,
  projectId,
  showAll,
  value,
  disabled = false,
}) => {
  const { data } = useGetEnvironmentsQuery({ projectId })
  const foundValue = useMemo(
    () => data?.results?.find((environment) => `${environment.id}` === value),
    [value, data],
  )
  return (
    <Select
      value={
        foundValue
          ? { label: foundValue.name, value: `${foundValue.id}` }
          : {
              label: disabled 
                ? 'Select a project first' 
                : (showAll ? 'All Environments' : 'Select a Environment'),
              value: '',
            }
      }
      options={(showAll
        ? [{ label: 'All Environments', value: '' }]
        : []
      ).concat(
        (data?.results || [])?.map((v) => ({
          label: v.name,
          value: `${v.id}`,
        })),
      )}
      onChange={(value: { value: string; label: string }) =>
        onChange(value?.value || '')
      }
      isDisabled={disabled}
    />
  )
}

export default EnvironmentFilter
