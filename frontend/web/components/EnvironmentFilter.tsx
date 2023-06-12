import { FC, useMemo } from 'react'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import ignore from 'ignore'

export type EnvironmentFilterType = {
  projectId: string
  value?: string
  onChange: (value: string) => void
  showAll?: boolean

  idField?: 'id' | 'api_key'
  ignore?: string[]
}

const EnvironmentFilter: FC<EnvironmentFilterType> = ({
  idField = 'api_key',
  ignore,
  onChange,
  projectId,
  showAll,
  value,
}) => {
  const { data } = useGetEnvironmentsQuery({ projectId })
  const foundValue = useMemo(
    () =>
      data?.results?.find((environment) => `${environment[idField]}` === value),
    [value, data, idField],
  )
  const environments = useMemo(() => {
    return (data?.results || [])
      ?.map((v) => ({
        label: v.name,
        value: `${v[idField]}`,
      }))
      .filter((v) => {
        if (ignore) {
          return !ignore.includes(v.value)
        }
        return true
      })
  }, [data?.results, ignore, idField])
  return (
    <Select
      value={
        foundValue
          ? { label: foundValue.name, value: `${foundValue.id}` }
          : {
              label: showAll ? 'All Environments' : 'Select an Environment',
              value: '',
            }
      }
      options={(showAll
        ? [{ label: 'All Environments', value: '' }]
        : []
      ).concat(environments)}
      onChange={(value: { value: string; label: string }) =>
        onChange(value?.value || '')
      }
    />
  )
}

export default EnvironmentFilter
