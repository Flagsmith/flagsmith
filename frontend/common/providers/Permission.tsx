import React, { FC, ReactNode, useMemo } from 'react'
import { useGetPermissionQuery } from 'common/services/usePermission'
import { PermissionLevel } from 'common/types/requests'
import AccountStore from 'common/stores/account-store'
import intersection from 'lodash/intersection'
import { cloneDeep } from 'lodash'
import Utils from 'common/utils/utils'
import Constants from 'common/constants'

type PermissionType = {
  id: any
  permission: string
  tags?: number[]
  level: PermissionLevel
  children:
    | ReactNode
    | ((data: { permission: boolean; isLoading: boolean }) => ReactNode)

  // New optional props from PermissionGate
  fallback?: ReactNode
  permissionName?: string
  showTooltip?: boolean
}

export const useHasPermission = ({
  id,
  level,
  permission,
  tags,
}: Omit<PermissionType, 'children'>) => {
  const {
    data: permissionsData,
    isLoading,
    isSuccess,
  } = useGetPermissionQuery({ id: `${id}`, level }, { skip: !id || !level })
  const data = useMemo(() => {
    if (!tags?.length || !permissionsData?.tag_based_permissions)
      return permissionsData
    const addedPermissions = cloneDeep(permissionsData)
    permissionsData.tag_based_permissions.forEach((tagBasedPermission) => {
      if (intersection(tagBasedPermission.tags, tags).length) {
        tagBasedPermission.permissions.forEach((key) => {
          addedPermissions[key] = true
        })
      }
    })
    return addedPermissions
  }, [permissionsData, tags])
  const hasPermission = !!data?.[permission] || !!data?.ADMIN
  return {
    isLoading,
    isSuccess,
    permission: !!hasPermission || !!AccountStore.isAdmin(),
  }
}

const Permission: FC<PermissionType> = ({
  children,
  fallback,
  id,
  level,
  permission,
  permissionName,
  showTooltip = false,
  tags,
}) => {
  const { isLoading, permission: hasPermission } = useHasPermission({
    id,
    level,
    permission,
    tags,
  })

  const finalPermission = hasPermission || AccountStore.isAdmin()

  if (typeof children === 'function') {
    return (
      <>
        {children({
          isLoading,
          permission: finalPermission,
        }) || null}
      </>
    )
  }

  if (finalPermission) {
    return <>{children}</>
  }

  if (showTooltip) {
    return Utils.renderWithPermission(
      finalPermission,
      permissionName || Constants.projectPermissions(permission),
      children,
    )
  }

  return <>{fallback || null}</>
}

export default Permission
