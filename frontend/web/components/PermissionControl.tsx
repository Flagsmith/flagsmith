import React from 'react'
import Select, { components } from 'react-select'
import Switch from './Switch'
import Tooltip from './Tooltip'
import BooleanDotIndicator from './BooleanDotIndicator'
import Icon from './Icon'
import { Permission } from 'common/types/responses'

const permissionOptions = [
  { label: 'Granted', value: 'GRANTED' },
  { label: 'Granted for tags', value: 'GRANTED_FOR_TAGS' },
  { label: 'None', value: 'NONE' },
]

const SingleValue = (props: any) => {
  return (
    <components.SingleValue {...props}>
      <div className='d-flex gap-1 align-items-center'>
        {props.data.value === 'GRANTED' && (
          <Icon width={18} name='checkmark' fill='#27AB95' />
        )}
        {props.data.value === 'GRANTED_FOR_TAGS' && (
          <Icon width={18} name='shield' fill='#ff9f43' />
        )}
        {props.children}
      </div>
    </components.SingleValue>
  )
}

interface PermissionControlProps {
  isTagBasedPermissions?: boolean
  isDebug?: boolean
  disabled: boolean
  isAdmin?: boolean
  isSaving?: boolean
  permissionType: string
  permissionKey: string
  isPermissionEnabled: boolean
  matchingPermission?: Permission
  supportsTag: boolean
  onValueChanged: (changed: boolean) => void
  onSelectPermissions: (
    key: string,
    type: 'GRANTED' | 'GRANTED_FOR_TAGS' | 'NONE',
  ) => void
  onTogglePermission: (key: string) => void
}

const PermissionControl: React.FC<PermissionControlProps> = ({
  disabled,
  isAdmin,
  isDebug = false,
  isPermissionEnabled,
  isSaving,
  isTagBasedPermissions = false,
  matchingPermission,
  onSelectPermissions,
  onTogglePermission,
  onValueChanged,
  permissionKey,
  permissionType,
  supportsTag,
}) => {
  if (isTagBasedPermissions) {
    return (
      <div className='ms-2' style={{ width: 200 }}>
        <Select<{ value: string }>
          value={permissionOptions.find((v) => v.value === permissionType)}
          onChange={(selectedOption) => {
            if (selectedOption && 'value' in selectedOption) {
              onValueChanged(true)
              onSelectPermissions(
                permissionKey,
                selectedOption.value as 'GRANTED' | 'GRANTED_FOR_TAGS' | 'NONE',
              )
            }
          }}
          className='react-select select-sm'
          disabled={disabled || isAdmin || isSaving}
          options={
            supportsTag
              ? permissionOptions
              : permissionOptions.filter((v) => v.value !== 'GRANTED_FOR_TAGS')
          }
          components={{ SingleValue }}
        />
      </div>
    )
  }

  if (isAdmin && isDebug)
    return <BooleanDotIndicator enabled={isPermissionEnabled} />

  if (isDebug) {
    return (
      <Tooltip title={<BooleanDotIndicator enabled={isPermissionEnabled} />}>
        {isPermissionEnabled &&
        matchingPermission?.is_directly_granted === false
          ? 'This permission is set by a group or a role'
          : ''}
      </Tooltip>
    )
  }

  return (
    <Switch
      data-test={`permission-switch-${permissionKey}`}
      onChange={() => {
        onValueChanged(true)
        onTogglePermission(permissionKey)
      }}
      disabled={disabled || isAdmin || isSaving || isDebug}
      checked={!disabled && isPermissionEnabled}
    />
  )
}

export default PermissionControl
