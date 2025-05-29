import React from 'react'
import { AvailablePermission } from 'common/types/responses'
import { PermissionLevel } from 'common/types/requests'
import { useGetUserPermissionsQuery } from 'common/services/useUserPermissions'
import PanelSearch from 'components/PanelSearch'
import Format from 'common/utils/format'

import { PermissionRow } from 'components/PermissionRow'
import { useGetAvailablePermissionsQuery } from 'common/services/useAvailablePermissions'

import DerivedPermissionsList from 'components/derived-permissions/DerivedPermissionsList'
import BooleanDotIndicator from 'components/BooleanDotIndicator'

const Permissions = ({
  level,
  levelId,
  projectId,
  userId,
}: {
  level: PermissionLevel
  levelId: string
  userId?: number
  projectId?: number
  className?: string
}) => {
  const { data: userPermissions, isLoading: isLoadingPermissions } =
    useGetUserPermissionsQuery(
      { id: levelId, level, userId: userId },
      { refetchOnMountOrArgChange: true, skip: !level || !levelId || !userId },
    )

  const { data: permissions } = useGetAvailablePermissionsQuery({ level })

  if (
    !userPermissions ||
    !userPermissions.permissions ||
    !permissions ||
    isLoadingPermissions
  ) {
    return (
      <div className='modal-body text-center'>
        <Loader />
      </div>
    )
  }

  const isAdmin = userPermissions.admin
  const isDirectlyGrantedAdmin = userPermissions.is_directly_granted
  const isDerivedAdmin =
    userPermissions.derived_from?.groups.length > 0 ||
    userPermissions.derived_from?.roles.length > 0

  const getTooltipText = () => {
    if (isDerivedAdmin && isAdmin && isDirectlyGrantedAdmin) {
      return 'Admin privileges are directly granted and come from a group and/or role.'
    }
    if (isDerivedAdmin && isAdmin) {
      return 'Admin privileges come from a group and/or role.'
    }
    if (isAdmin && isDirectlyGrantedAdmin) {
      return 'Admin privileges directly granted.'
    }

    return ''
  }

  return (
    <div>
      {level !== 'organisation' && (
        <div className='my-2'>
          <Row>
            <Flex>
              <div className='font-weight-medium text-dark mb-1'>
                Administrator
              </div>
              {isDerivedAdmin && (
                <div>
                  <DerivedPermissionsList
                    derivedPermissions={userPermissions.derived_from}
                  />
                </div>
              )}
            </Flex>
            <div className='mr-3'>
              <Tooltip title={<BooleanDotIndicator enabled={isAdmin} />}>
                {getTooltipText()}
              </Tooltip>
            </div>
          </Row>
        </div>
      )}
      <PanelSearch
        filterRow={(item: AvailablePermission, search: string) => {
          const name = Format.enumeration.get(item.key).toLowerCase()
          return name.includes(search?.toLowerCase() || '')
        }}
        title='Permissions'
        className='no-pad mb-2 overflow-visible'
        items={permissions}
        renderRow={(p) => (
          <PermissionRow
            key={p.key}
            permission={p}
            level={level}
            projectId={projectId}
            entityPermissions={userPermissions}
            isAdmin={isAdmin}
            isTagBasedPermissions={false}
            onValueChanged={() => {}}
            onSelectPermissions={() => {}}
            isDebug
          />
        )}
      />
    </div>
  )
}

export default Permissions
