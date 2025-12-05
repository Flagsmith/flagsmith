import React, { FC, ReactNode } from 'react'
import Permission from 'common/providers/Permission'
import Utils from 'common/utils/utils'
import Constants from 'common/constants'

type PermissionLevel = 'project' | 'environment' | 'organisation'

interface PermissionGateProps {
  level: PermissionLevel
  permission: string
  id: string | number
  children: ReactNode | ((hasPermission: boolean) => ReactNode)
  fallback?: ReactNode
  permissionName?: string
  showTooltip?: boolean
}

/**
 * PermissionGate component standardizes permission checking across the application.
 *
 * Wraps content with permission checking logic and optionally shows tooltips
 * or fallback content when permission is denied.
 *
 * @param level - Permission level: 'project', 'environment', or 'organisation'
 * @param permission - The permission string to check (e.g., 'CREATE_FEATURE')
 * @param id - The ID of the resource (project/environment/organisation)
 * @param children - Content to render (can be ReactNode or render function)
 * @param fallback - Optional content to show when permission is denied
 * @param permissionName - Optional custom permission name for tooltip
 * @param showTooltip - Whether to show tooltip on permission denial (default: true)
 *
 * @example
 * ```tsx
 * // Simple usage
 * <PermissionGate level='project' permission='CREATE_FEATURE' id={projectId}>
 *   <Button>Create Feature</Button>
 * </PermissionGate>
 *
 * // With render function
 * <PermissionGate level='project' permission='CREATE_FEATURE' id={projectId}>
 *   {(hasPermission) => (
 *     <Button disabled={!hasPermission}>Create Feature</Button>
 *   )}
 * </PermissionGate>
 *
 * // With custom fallback
 * <PermissionGate
 *   level='project'
 *   permission='CREATE_FEATURE'
 *   id={projectId}
 *   fallback={<div>No permission</div>}
 *   showTooltip={false}
 * >
 *   <Button>Create Feature</Button>
 * </PermissionGate>
 * ```
 */
export const PermissionGate: FC<PermissionGateProps> = ({
  children,
  fallback,
  id,
  level,
  permission,
  permissionName,
  showTooltip = true,
}) => {
  return (
    <Permission level={level} permission={permission} id={id}>
      {({ permission: hasPermission }) => {
        // Handle render function pattern
        if (typeof children === 'function') {
          return children(hasPermission)
        }

        // If permission granted, render children
        if (hasPermission) {
          return <>{children}</>
        }

        // Permission denied - show tooltip or fallback
        if (showTooltip) {
          return Utils.renderWithPermission(
            hasPermission,
            permissionName || Constants.projectPermissions(permission),
            children,
          )
        }

        return <>{fallback || null}</>
      }}
    </Permission>
  )
}

export default PermissionGate
