import React, { FC, ReactNode, useMemo } from 'react'
import { useGetPermissionQuery } from 'common/services/usePermission'
import { PermissionLevel } from 'common/types/requests'
import AccountStore from 'common/stores/account-store'
import intersection from 'lodash/intersection'
import { add } from 'ionicons/icons'
import { cloneDeep } from 'lodash' // we need this to make JSX compile

type PermissionType = {
  id: any
  permission: string
  tags?: number[]
  level: PermissionLevel
  children: (data: { permission: boolean; isLoading: boolean }) => ReactNode
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
  id,
  level,
  permission,
  tags,
}) => {
  const { isLoading, permission: hasPermission } = useHasPermission({
    id,
    level,
    permission,
    tags,
  })
  return (
    <>
      {children({
        isLoading,
        permission: hasPermission || AccountStore.isAdmin(),
      }) || null}
    </>
  )
}

export default Permission
