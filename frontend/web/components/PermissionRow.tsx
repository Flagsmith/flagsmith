import React from 'react'
import Switch from './Switch'
import Select, { components } from 'react-select'
import AddEditTags from './tags/AddEditTags'
import Format from 'common/utils/format'
import Icon from './Icon'
import { SingleValueProps } from 'react-select/lib/components/SingleValue'
import {
  AvailablePermission,
  DerivedPermission,
  Permission,
  RolePermission,
  UserPermissions,
} from 'common/types/responses'
import DerivedPermissionsList from './DerivedPermissionsList'
import BooleanDotIndicator from './BooleanDotIndicator'

const permissionOptions = [
  { label: 'Granted', value: 'GRANTED' },
  { label: 'Granted for tags', value: 'GRANTED_FOR_TAGS' },
  { label: 'None', value: 'NONE' },
]

const SingleValue = (props: SingleValueProps<any>) => {
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

type EntityPermissions = Omit<
  RolePermission,
  'user' | 'id' | 'group' | 'isGroup'
> & {
  id?: number
  group?: number
  user?: number
  tags?: number[]
}

interface PermissionRowProps {
  permission: AvailablePermission
  level: string
  projectId?: string | number
  entityPermissions: EntityPermissions | UserPermissions
  onSelectPermissions: (
    key: string,
    type: 'GRANTED' | 'GRANTED_FOR_TAGS' | 'NONE',
    tags?: number[],
  ) => void
  onTogglePermission: (key: string) => void
  limitedPermissions?: string[]
  isTagBasedPermissions?: boolean
  isAdmin: boolean
  isSaving: boolean
  isDebug?: boolean
  onValueChanged: (changed: boolean) => void
}

export const PermissionRow: React.FC<PermissionRowProps> = ({
  entityPermissions,
  isAdmin,
  isDebug,
  isSaving,
  isTagBasedPermissions,
  level,
  limitedPermissions = [],
  onSelectPermissions,
  onTogglePermission,
  onValueChanged,
  permission,
  projectId,
}) => {
  const matchingPermission = entityPermissions.permissions.find(
    (e) => e.permission_key === permission.key,
  )

  console.log(matchingPermission)

  const hasPermission = (key: string) => {
    if (isAdmin) return true
    return entityPermissions.permissions.find(
      (permission) => permission.permission_key === key,
    )
  }

  const getPermissionType = (key: string) => {
    if (isAdmin) return 'GRANTED'
    const permission = entityPermissions.permissions.find(
      (v) => v.permission_key === key,
    )

    if (!permission) return 'NONE'

    if (permission.tags?.length || limitedPermissions.includes(key)) {
      return 'GRANTED_FOR_TAGS'
    }

    return 'GRANTED'
  }

  const levelUpperCase = level.toUpperCase()

  const disabled =
    level !== 'organisation' &&
    permission.key !== `VIEW_${levelUpperCase}` &&
    !hasPermission(`VIEW_${levelUpperCase}`)

  const permissionData = entityPermissions.permissions.find(
    (v) => v.permission_key === permission.key,
  )

  const permissionType = getPermissionType(permission.key)

  const isPermissionEnabled = !!hasPermission(permission.key)

  return (
    <Row
      key={permission.key}
      style={isAdmin && !isDebug ? { opacity: 0.5 } : undefined}
      className='list-item list-item-sm px-3 py-2'
    >
      <Row space>
        <Flex>
          <strong>{Format.enumeration.get(permission.key)}</strong>
          <div className='list-item-subtitle'>{permission.description}</div>
          {permissionType === 'GRANTED_FOR_TAGS' && (
            <AddEditTags
              projectId={`${projectId}`}
              value={permissionData?.tags || []}
              onChange={(v: number[]) => {
                onValueChanged(true)
                onSelectPermissions(permission.key, 'GRANTED_FOR_TAGS', v)
              }}
            />
          )}
          {isDebug && (
            <div className='mt-2'>
              <DerivedPermissionsList
                isAdmin={isAdmin}
                derivedPermissions={
                  (matchingPermission as Permission)?.derived_from
                }
              />
            </div>
          )}
        </Flex>
        {isTagBasedPermissions ? (
          <div className='ms-2' style={{ width: 200 }}>
            <Select<{ value: string }>
              value={permissionOptions.find((v) => v.value === permissionType)}
              onChange={(selectedOption) => {
                if (selectedOption && 'value' in selectedOption) {
                  onValueChanged(true)
                  onSelectPermissions(
                    permission.key,
                    selectedOption.value as
                      | 'GRANTED'
                      | 'GRANTED_FOR_TAGS'
                      | 'NONE',
                  )
                }
              }}
              className='react-select select-sm'
              disabled={disabled || isAdmin || isSaving}
              options={
                permission.supports_tag
                  ? permissionOptions
                  : permissionOptions.filter(
                      (v) => v.value !== 'GRANTED_FOR_TAGS',
                    )
              }
              components={{ SingleValue }}
            />
          </div>
        ) : isDebug ? (
          <Tooltip
            title={<BooleanDotIndicator enabled={isPermissionEnabled} />}
          >
            {isPermissionEnabled &&
            (matchingPermission as Permission)?.is_directly_granted === false
              ? 'This permission is set by a group or a role'
              : ''}
          </Tooltip>
        ) : (
          <Switch
            data-test={`permission-switch-${permission.key}`}
            onChange={() => {
              onValueChanged(true)
              onTogglePermission(permission.key)
            }}
            disabled={disabled || isAdmin || isSaving || isDebug}
            checked={!disabled && hasPermission(permission.key)}
          />
        )}
      </Row>
    </Row>
  )
}
