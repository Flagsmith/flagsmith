import React, { FC, useMemo } from 'react'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { Props } from 'react-select/lib/Select'
import Tag from './tags/Tag'
import Utils from 'common/utils/utils'

export type EnvironmentSelectType = Omit<
  Partial<Props>,
  'value' | 'onChange'
> & {
  projectId: string
  value?: string[] | string | null
  onChange: (value: string[] | string | undefined) => void
  idField?: 'id' | 'api_key'
  dataTest?: (value: { label: string }) => string
  multiple?: boolean
  allowEmpty?: boolean
}

const EnvironmentSelect: FC<EnvironmentSelectType> = ({
  allowEmpty = false,
  idField = 'api_key',
  ignore,
  multiple = false,
  onChange,
  projectId,
  value,
}) => {
  const { data } = useGetEnvironmentsQuery({ projectId: `${projectId}` })
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
    <Row className='mb-2'>
      {environments.map((env, i) => (
        <Tag
          tag={{
            color: Utils.getTagColour(i),
            label: env.label,
          }}
          key={env.value}
          selected={
            multiple
              ? Array.isArray(value) && value.includes(env.value)
              : value === env.value
          }
          onClick={() => {
            if (multiple) {
              if (Array.isArray(value) && value.includes(env.value)) {
                const newValue = value.filter((v) => v !== env.value)
                onChange(allowEmpty && newValue.length === 0 ? [] : newValue)
              } else {
                onChange((value || []).concat([env.value]))
              }
            } else {
              onChange(
                value === env.value
                  ? allowEmpty
                    ? undefined
                    : value
                  : env.value,
              )
            }
          }}
          className='mr-2 mb-2'
        />
      ))}
    </Row>
  )
}

export default EnvironmentSelect
