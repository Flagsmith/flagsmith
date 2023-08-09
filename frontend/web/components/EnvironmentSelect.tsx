import React, { FC, useMemo } from 'react'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'

export type EnvironmentSelectType = {
  projectId: string
  value?: string
  onChange: (value: string) => void
  showAll?: boolean
  readOnly?: boolean
  idField?: 'id' | 'api_key'
  ignore?: string[]
}

const EnvironmentSelect: FC<EnvironmentSelectType> = ({
  idField = 'api_key',
  ignore,
  onChange,
  projectId,
  readOnly,
  showAll,
  value,
}) => {
  const { data } = useGetEnvironmentsQuery({ projectId: `${projectId}` })
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
  if (readOnly) {
    return <div className='mb-2'>{foundValue?.name}</div>
  }
  return (
    <div>
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
    </div>
  )
}

export default EnvironmentSelect
