import React, { FC, useMemo } from 'react'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { Props } from 'react-select/lib/Select'
import Tag from './tags/Tag'
import Utils from 'common/utils/utils'
import Button from './base/forms/Button'

export type EnvironmentSelectType = Omit<
  Partial<Props>,
  'value' | 'onChange'
> & {
  projectId: string | number | undefined
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

  const handleSelectAll = () => {
    if (multiple) {
      onChange(environments.map((env) => env.value))
    }
  }

  const handleClearAll = () => {
    if (multiple) {
      onChange(allowEmpty ? [] : undefined)
    }
  }

  const selectedCount = Array.isArray(value) ? value.length : 0
  const allSelected = selectedCount === environments.length

  return (
    <div className='d-flex align-items-center mb-2'>
      <Row className='flex-1 row-gap-1'>
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
            className='mb-2 chip--xs'
          />
        ))}
      </Row>
      {multiple && environments.length > 0 && (
        <div
          className='flex-shrink-0 ml-2 text-right'
          style={{ width: '140px' }}
        >
          {!allSelected && (
            <Button
              onClick={handleSelectAll}
              size='xSmall'
              theme='text'
              className='mr-2'
            >
              Select All
            </Button>
          )}
          {selectedCount > 1 && (
            <Button onClick={handleClearAll} size='xSmall' theme='text'>
              Clear
            </Button>
          )}
        </div>
      )}
    </div>
  )
}

export default EnvironmentSelect
