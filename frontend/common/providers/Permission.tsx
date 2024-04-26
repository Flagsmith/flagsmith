import React, { FC, ReactNode } from 'react'
import { useGetPermissionQuery } from 'common/services/usePermission'
import { PermissionLevel } from 'common/types/requests'
import AccountStore from 'common/stores/account-store' // we need this to make JSX compile

type PermissionType = {
  id: any
  permission: string
  level: PermissionLevel
  children: (data: { permission: boolean; isLoading: boolean }) => ReactNode
}

export const useHasPermission = ({
  id,
  level,
  permission,
}: Omit<PermissionType, 'children'>) => {
  const { data, isLoading } = useGetPermissionQuery(
    { id: `${id}`, level },
    { skip: !id || !level },
  )
  const hasPermission = !!data?.[permission] || !!data?.ADMIN
  return { isLoading, permission: !!hasPermission || !!AccountStore.isAdmin() }
}

const Permission: FC<PermissionType> = ({
  children,
  id,
  level,
  permission,
}) => {
  const { isLoading, permission: hasPermission } = useHasPermission({
    id,
    level,
    permission,
  })
  return (
    <>
      {children({
        isLoading,
        permission: hasPermission || AccountStore.isAdmin(),
      }) || <div />}
    </>
  )
}

export default Permission
