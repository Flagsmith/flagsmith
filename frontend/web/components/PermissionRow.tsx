import React from 'react'
import AddEditTags from './tags/AddEditTags'
import Format from 'common/utils/format'

import {
  AvailablePermission,
  Permission,
  RolePermission,
  UserPermissions,
} from 'common/types/responses'
import DerivedPermissionsList from './derived-permissions/DerivedPermissionsList'
import PermissionControl from './PermissionControl'
import { PermissionRoleType } from 'common/types/requests'

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
    type: PermissionRoleType,
    tags?: number[],
  ) => void
  limitedPermissions?: string[]
  isTagBasedPermissions?: boolean
  isAdmin?: boolean
  isSaving?: boolean
  isDebug?: boolean
  hasPermission: (key: string) => boolean
  onValueChanged: (permissionKey: string, shouldToggle?: boolean) => void
}

export const PermissionRow: React.FC<PermissionRowProps> = ({
  entityPermissions,
  isAdmin,
  isDebug,
  isSaving,
  isTagBasedPermissions,
  level,
  limitedPermissions = [],
  hasPermission,
  onSelectPermissions,
  onValueChanged,
  permission,
  projectId,
}) => {
  const matchingPermission = entityPermissions.permissions.find(
    (e) => e.permission_key === permission.key,
  )


  const getPermissionRoleType = (key: string) => {
    if (isAdmin) return PermissionRoleType.GRANTED
    const permission = entityPermissions.permissions.find(
      (v) => v.permission_key === key,
    )

    if (!permission) return PermissionRoleType.NONE

    if (permission.tags?.length || limitedPermissions.includes(key)) {
      return PermissionRoleType.GRANTED_FOR_TAGS
    }

    return PermissionRoleType.GRANTED
  }

  const requiresViewPermission = (permissionKey: string) => {
    return (
      level !== 'organisation' &&
      permissionKey !== `VIEW_${level.toUpperCase()}`
    )
  }

  const levelUpperCase = level.toUpperCase()
  const viewPermission = `VIEW_${levelUpperCase}`


  const disabled =
    level !== 'organisation' &&
    permission.key !== `VIEW_${levelUpperCase}` &&
    !hasPermission(`VIEW_${levelUpperCase}`)

  const permissionData = entityPermissions.permissions.find(
    (v) => v.permission_key === permission.key,
  )

  const permissionRoleType = getPermissionRoleType(permission.key)

  const showDerivedPermissions =
    isDebug && (matchingPermission as Permission)?.is_directly_granted === false

  const isRowDisabled = isAdmin && !isDebug
  const rowStyle = isRowDisabled ? { opacity: 0.5 } : {}

  return (
    <Row
      key={permission.key}
      style={rowStyle}
      className='list-item list-item-sm px-3 py-2 cursor-default'
    >
      <Row space>
        <Flex>
          <strong>{Format.enumeration.get(permission.key)}</strong>
          <div className='list-item-subtitle'>{permission.description}</div>
          {permissionRoleType === PermissionRoleType.GRANTED_FOR_TAGS && (
            <AddEditTags
              projectId={`${projectId}`}
              value={permissionData?.tags || []}
              onChange={(v: number[]) => {
                onValueChanged(permission.key, false)
                onSelectPermissions(permission.key, PermissionRoleType.GRANTED_FOR_TAGS, v)
              }}
            />
          )}
          {showDerivedPermissions && (
            <div className='mt-2'>
              <DerivedPermissionsList
                derivedPermissions={
                  (matchingPermission as Permission)?.derived_from
                }
              />
            </div>
          )}
        </Flex>
        <PermissionControl
          isTagBasedPermissions={isTagBasedPermissions}
          isDebug={isDebug}
          disabled={disabled}
          isAdmin={isAdmin}
          isSaving={isSaving}
          permissionRoleType={permissionRoleType}
          permissionKey={permission.key}
          isViewPermissionRequired={requiresViewPermission(permission.key)}
          isViewPermissionAllowed={hasPermission(viewPermission)}
          isPermissionEnabled={hasPermission(permission.key)}
          supportsTag={permission.supports_tag}
          onValueChanged={onValueChanged}
          onSelectPermissions={onSelectPermissions}
        />
      </Row>
    </Row>
  )
}
