import React, { FC, useMemo } from 'react'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { Props } from 'react-select/lib/Select'
import { Environment } from 'common/types/responses'

export type EnvironmentSelectType = Partial<Omit<Props, 'value'>> & {
  projectId: number
  value?: string
  label?: string
  onChange: (value: string, environment: Environment | null) => void
  showAll?: boolean
  readOnly?: boolean
  idField?: 'id' | 'api_key'
  ignore?: string[]
  dataTest?: (value: { label: string }) => string
}

const EnvironmentSelect: FC<EnvironmentSelectType> = ({
  idField = 'api_key',
  ignore,
  label,
  onChange,
  projectId,
  readOnly,
  showAll,
  value,
  ...rest
}) => {
  const { data } = useGetEnvironmentsQuery({ projectId: `${projectId}` })

  const environments = useMemo(() => {
    return (data?.results || [])
      ?.map((v) => ({
        environment: v,
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

  const foundValue = useMemo(
    () =>
      environments.find((environment) => `${environment.value}` === `${value}`),
    [value, environments],
  )

  if (readOnly) {
    return <div className='mb-2'>{foundValue?.label}</div>
  }
  return (
    <div>
      <Select
        {...rest}
        className='react-select select-xsm'
        value={
          foundValue
            ? foundValue
            : {
                label:
                  label ||
                  (showAll ? 'All Environments' : 'Select an Environment'),
                value: '',
              }
        }
        options={(showAll
          ? [{ environment: null, label: 'All Environments', value: '' }]
          : []
        ).concat(environments)}
        onChange={(value: {
          value: string
          label: string
          environment: Environment
        }) => onChange(value?.value || '', value?.environment)}
      />
    </div>
  )
}

export default EnvironmentSelect
