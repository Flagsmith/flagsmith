import React, { FC, ReactNode, useMemo } from 'react'
import { useGetPermissionQuery } from 'common/services/usePermission'
import { PermissionLevel } from 'common/types/requests'
import AccountStore from 'common/stores/account-store'
import intersection from 'lodash/intersection'
import { cloneDeep } from 'lodash'
import Utils from 'common/utils/utils'
import Constants from 'common/constants'

/**
 * Props for the Permission component
 *
 * @property {number | string} id - The ID of the resource (projectId, organisationId, environmentId, etc.)
 * @property {string} permission - The permission key to check (e.g., 'CREATE_FEATURE', 'UPDATE_FEATURE')
 * @property {PermissionLevel} level - The permission level ('project', 'organisation', 'environment')
 * @property {number[]} [tags] - Optional tag IDs for tag-based permission checking
 * @property {ReactNode | ((data: { permission: boolean; isLoading: boolean }) => ReactNode)} children - Content to render or render function
 * @property {ReactNode} [fallback] - Optional content to render when permission is denied
 * @property {string} [permissionName] - Optional custom permission name for tooltip display
 * @property {boolean} [showTooltip=false] - Whether to show a tooltip when permission is denied
 */
type PermissionType = {
  id: number | string
  permission: string
  tags?: number[]
  level: PermissionLevel
  children:
    | ReactNode
    | ((data: { permission: boolean; isLoading: boolean }) => ReactNode)
  fallback?: ReactNode
  permissionName?: string
  showTooltip?: boolean
}

/**
 * Hook to check if the current user has a specific permission
 *
 * Fetches permission data and checks if the user has the requested permission.
 * Supports tag-based permissions where additional permissions can be granted
 * based on tag intersection.
 *
 * @param {Object} params - The permission check parameters
 * @param {number | string} params.id - The resource ID to check permissions for
 * @param {PermissionLevel} params.level - The permission level to check at
 * @param {string} params.permission - The permission key to check
 * @param {number[]} [params.tags] - Optional tag IDs for tag-based permission checking
 * @returns {Object} Object containing permission status and loading state
 * @returns {boolean} returns.isLoading - Whether the permission data is still loading
 * @returns {boolean} returns.isSuccess - Whether the permission data was fetched successfully
 * @returns {boolean} returns.permission - Whether the user has the requested permission
 */
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

/**
 * Permission component for conditional rendering based on user permissions
 *
 * This component checks if the current user has a specific permission and conditionally
 * renders its children. It supports multiple rendering patterns:
 *
 * @example
 * // Basic usage with simple children
 * <Permission level="project" permission="CREATE_FEATURE" id={projectId}>
 *   <Button>Create Feature</Button>
 * </Permission>
 *
 * @example
 * // Using render function to access permission state
 * <Permission level="project" permission="CREATE_FEATURE" id={projectId}>
 *   {({ permission, isLoading }) => (
 *     <Button disabled={!permission || isLoading}>Create Feature</Button>
 *   )}
 * </Permission>
 *
 * @example
 * // With tooltip on permission denial
 * <Permission
 *   level="project"
 *   permission="CREATE_FEATURE"
 *   id={projectId}
 *   showTooltip
 *   permissionName="Create Features"
 * >
 *   <Button>Create Feature</Button>
 * </Permission>
 *
 * @example
 * // With fallback content
 * <Permission
 *   level="project"
 *   permission="DELETE_FEATURE"
 *   id={projectId}
 *   fallback={<Text>You don't have permission to delete features</Text>}
 * >
 *   <Button>Delete Feature</Button>
 * </Permission>
 *
 * @example
 * // With tag-based permissions
 * <Permission
 *   level="project"
 *   permission="UPDATE_FEATURE"
 *   id={projectId}
 *   tags={[tagId1, tagId2]}
 * >
 *   <Button>Update Feature</Button>
 * </Permission>
 */
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
    const renderedChildren = children({
      isLoading,
      permission: finalPermission,
    })

    if (finalPermission || !showTooltip) {
      return <>{renderedChildren || null}</>
    }

    return Utils.renderWithPermission(
      finalPermission,
      permissionName || Constants.projectPermissions(permission),
      renderedChildren,
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
