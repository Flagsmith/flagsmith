import React, { FC, ReactNode, useMemo } from 'react'
import { useGetPermissionQuery } from 'common/services/usePermission'
import AccountStore from 'common/stores/account-store'
import intersection from 'lodash/intersection'
import { cloneDeep } from 'lodash'
import Utils from 'common/utils/utils'
import Constants from 'common/constants'
import {
  ADMIN_PERMISSION,
  EnvironmentPermission,
  OrganisationPermission,
  ProjectPermission,
} from 'common/types/permissions.types'

/**
 * Base props shared across all permission levels
 */
type BasePermissionProps = {
  id: number | string
  tags?: number[]
  children:
    | ReactNode
    | ((data: { permission: boolean; isLoading: boolean }) => ReactNode)
  fallback?: ReactNode
  permissionName?: string
  showTooltip?: boolean
}

/**
 * Discriminated union types for each permission level
 * This means we can detect a mismatch between level and permission
 */
type OrganisationLevelProps = BasePermissionProps & {
  level: 'organisation'
  permission: OrganisationPermission
}

type ProjectLevelProps = BasePermissionProps & {
  level: 'project'
  permission: ProjectPermission
}

type EnvironmentLevelProps = BasePermissionProps & {
  level: 'environment'
  permission: EnvironmentPermission
}

type PermissionType =
  | OrganisationLevelProps
  | ProjectLevelProps
  | EnvironmentLevelProps

type UseHasPermissionParams = {
  id: number | string
  level: 'organisation' | 'project' | 'environment'
  permission: OrganisationPermission | ProjectPermission | EnvironmentPermission
  tags?: number[]
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
}: UseHasPermissionParams) => {
  const {
    data: permissionsData,
    isLoading,
    isSuccess,
  } = useGetPermissionQuery(
    { id: id as number, level },
    { skip: !id || !level },
  )
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

  const getPermissionDescription = (): string => {
    if (permission === ADMIN_PERMISSION) {
      switch (level) {
        case 'environment':
          return Constants.environmentPermissions(ADMIN_PERMISSION)
        case 'project':
          return Constants.projectPermissions(ADMIN_PERMISSION)
        default:
          return Constants.organisationPermissions(ADMIN_PERMISSION)
      }
    }

    switch (level) {
      case 'environment':
        return Constants.environmentPermissions(
          permission as EnvironmentPermission,
        )
      case 'project':
        return Constants.projectPermissions(permission as ProjectPermission)
      default:
        return Constants.organisationPermissions(
          permission as OrganisationPermission,
        )
    }
  }

  const tooltipMessage = permissionName || getPermissionDescription()

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
      tooltipMessage,
      renderedChildren,
    )
  }

  if (finalPermission) {
    return <>{children}</>
  }

  if (showTooltip) {
    return Utils.renderWithPermission(finalPermission, tooltipMessage, children)
  }

  return <>{fallback || null}</>
}

export default Permission
