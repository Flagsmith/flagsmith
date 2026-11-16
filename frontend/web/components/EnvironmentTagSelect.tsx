import React, { FC, useMemo } from 'react'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import ToggleChip from './base/ToggleChip'
import ColorSwatch from './ColorSwatch'
import { getEnvironmentColour } from 'common/utils/environmentColour'
import Button from './base/forms/Button'

type EnvironmentSelectType = {
  projectId: string | number | undefined
  value?: string[] | string | null
  onChange: (value: string[] | string | undefined) => void
  idField?: 'id' | 'api_key'
  dataTest?: (value: { label: string }) => string
  multiple?: boolean
  allowEmpty?: boolean
  ignore?: string[]
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
  const { data } = useGetEnvironmentsQuery({ projectId: Number(projectId) })
  const environments = useMemo(() => {
    return (data?.results || [])
      ?.map((v, i) => ({
        // Position in the whole list, before `ignore`, as other screens use.
        colour: getEnvironmentColour(v, i),
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

  // Single mode picks one; clicking it again clears it only when allowEmpty.
  const toggle = (envValue: string) => {
    if (multiple) {
      const current = Array.isArray(value) ? value : []
      onChange(
        current.includes(envValue)
          ? current.filter((v) => v !== envValue)
          : [...current, envValue],
      )
      return
    }
    if (value !== envValue) {
      onChange(envValue)
    } else if (allowEmpty) {
      onChange(undefined)
    }
  }

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
      <Row
        role='group'
        aria-label='Environments'
        className='flex-1 row-gap-1 gap-1'
      >
        {environments.map((env) => (
          <ToggleChip
            key={env.value}
            size='sm'
            className='mb-2'
            checked={
              multiple
                ? Array.isArray(value) && value.includes(env.value)
                : value === env.value
            }
            onChange={() => toggle(env.value)}
          >
            <ColorSwatch color={env.colour} shape='circle' size='sm' />
            {env.label}
          </ToggleChip>
        ))}
      </Row>
      {multiple && environments.length > 0 && (
        <div className='flex-shrink-0 text-right' style={{ width: '140px' }}>
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
