import React, { useMemo } from 'react'
import Select, { components } from 'react-select'
import Switch from './Switch'
import Tooltip from './Tooltip'
import BooleanDotIndicator from './BooleanDotIndicator'
import Icon from './Icon'
import { PermissionRoleType } from 'common/types/requests'

const permissionOptions = [
  { label: 'Granted', value: PermissionRoleType.GRANTED },
  { label: 'Granted for tags', value: PermissionRoleType.GRANTED_FOR_TAGS },
  { label: 'None', value: PermissionRoleType.NONE },
]

const ADMIN_PERMISSION_TEXT = 'This permission comes from admin privileges'
const ADMIN_AND_DERIVED_PERMISSION_TEXT = `${ADMIN_PERMISSION_TEXT} and is inherited through a group and/or role.`
const DERIVED_PERMISSION_TEXT =
  'This permission is inherited via a group and/or role.'
const DIRECTLY_GRANTED_PERMISSION_TEXT =
  'This permission is directly assigned to the user'
const DIRECTLY_GRANTED_AND_DERIVED_PERMISSION_TEXT = `${DIRECTLY_GRANTED_PERMISSION_TEXT} and is also inherited through a group and/or role.`

const SingleValue = (props: any) => {
  return (
    <components.SingleValue {...props}>
      <div className='d-flex gap-1 align-items-center'>
        {props.data.value === PermissionRoleType.GRANTED && (
          <Icon width={18} name='checkmark' fill='#27AB95' />
        )}
        {props.data.value === PermissionRoleType.GRANTED_FOR_TAGS && (
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
  isDirectlyGranted?: boolean
  showDerivedPermission?: boolean
  isSaving?: boolean
  permissionRoleType: PermissionRoleType
  permissionKey: string
  isViewPermissionRequired?: boolean
  isViewPermissionAllowed?: boolean
  isPermissionEnabled: boolean
  supportsTag: boolean
  onValueChanged: (permissionKey: string, shouldToggle?: boolean) => void
  onSelectPermissions: (key: string, type: PermissionRoleType) => void
}

const PermissionControl: React.FC<PermissionControlProps> = ({
  disabled,
  isAdmin,
  isDebug = false,
  isDirectlyGranted,
  isPermissionEnabled,
  isSaving,
  isTagBasedPermissions = false,
  isViewPermissionAllowed,
  isViewPermissionRequired,
  onSelectPermissions,
  onValueChanged,
  permissionKey,
  permissionRoleType,
  showDerivedPermission,
  supportsTag,
}) => {
  const tooltipText = useMemo(() => {
    if (isAdmin) {
      return showDerivedPermission
        ? ADMIN_AND_DERIVED_PERMISSION_TEXT
        : ADMIN_PERMISSION_TEXT
    }

    if (isDirectlyGranted) {
      return showDerivedPermission
        ? DIRECTLY_GRANTED_AND_DERIVED_PERMISSION_TEXT
        : DIRECTLY_GRANTED_PERMISSION_TEXT
    }

    return showDerivedPermission ? DERIVED_PERMISSION_TEXT : ''
  }, [isAdmin, showDerivedPermission, isDirectlyGranted])

  if (isTagBasedPermissions) {
    return (
      <div className='ms-2' style={{ width: 200 }}>
        <Select<{ value: PermissionRoleType }>
          value={permissionOptions.find((v) => v.value === permissionRoleType)}
          onChange={(selectedOption) => {
            if (selectedOption && 'value' in selectedOption) {
              onValueChanged(permissionKey, false)
              onSelectPermissions(
                permissionKey,
                selectedOption.value as PermissionRoleType,
              )
            }
          }}
          className='react-select select-sm'
          disabled={disabled || isAdmin || isSaving}
          options={
            supportsTag
              ? permissionOptions
              : permissionOptions.filter(
                  (v) => v.value !== PermissionRoleType.GRANTED_FOR_TAGS,
                )
          }
          components={{ SingleValue }}
        />
      </div>
    )
  }

  if (isDebug) {
    return (
      <Tooltip title={<BooleanDotIndicator enabled={isPermissionEnabled} />}>
        {tooltipText}
      </Tooltip>
    )
  }

  const isViewRequiredAndNotAllowed =
    isViewPermissionRequired && !isViewPermissionAllowed
  const isChecked =
    !disabled &&
    isPermissionEnabled &&
    (!isViewPermissionRequired || isViewPermissionAllowed)

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
