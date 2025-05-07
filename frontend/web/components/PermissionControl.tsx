import React, { useMemo } from 'react'
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
  isDerivedPermission?: boolean
  isSaving?: boolean
  permissionType: string
  permissionKey: string
  isViewPermissionRequired?: boolean
  isViewPermissionAllowed?: boolean
  isPermissionEnabled: boolean
  supportsTag: boolean
  onValueChanged: (permissionKey: string, shouldToggle?: boolean) => void
  onSelectPermissions: (
    key: string,
    type: 'GRANTED' | 'GRANTED_FOR_TAGS' | 'NONE',
  ) => void
}

const PermissionControl: React.FC<PermissionControlProps> = ({
  disabled,
  isAdmin,
  isDebug = false,
  isDerivedPermission,
  isPermissionEnabled,
  isSaving,
  isTagBasedPermissions = false,
  isViewPermissionAllowed,
  isViewPermissionRequired,
  onSelectPermissions,
  onValueChanged,
  permissionKey,
  permissionType,
  supportsTag,
}) => {
  const tooltipText = useMemo(() => {
    if (isAdmin && !isDerivedPermission) {
      return 'This permission comes from admin privileges'
    }

    if (isAdmin && isDerivedPermission) {
      return 'This permission comes from admin privileges and is inherited via a group and/or role.'
    }

    if (!isAdmin && isDerivedPermission) {
      return 'This permission is inherited via a group and/or role.'
    }

    return ''
  }, [isAdmin, isDerivedPermission])

  if (isTagBasedPermissions) {
    return (
      <div className='ms-2' style={{ width: 200 }}>
        <Select<{ value: string }>
          value={permissionOptions.find((v) => v.value === permissionType)}
          onChange={(selectedOption) => {
            if (selectedOption && 'value' in selectedOption) {
              onValueChanged(permissionKey, false)
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

  //   if (isAdmin && isDebug)
  //     return <BooleanDotIndicator enabled={isPermissionEnabled} />

  if (isDebug) {
    return (
      <Tooltip title={<BooleanDotIndicator enabled={isPermissionEnabled} />}>
        {tooltipText}
      </Tooltip>
    )
  }

  const isViewRequiredAndNotAllowed =
    isViewPermissionRequired && !isViewPermissionAllowed
  const isChecked = !disabled && isPermissionEnabled && (!isViewPermissionRequired || isViewPermissionAllowed)

  return (
    <Switch
      data-test={`permission-switch-${permissionKey}`}
      onChange={() => {
        onValueChanged(permissionKey, true)
      }}
      disabled={isViewRequiredAndNotAllowed || isAdmin || isSaving || isDebug}
      checked={isChecked}
    />
  )
}

export default PermissionControl
