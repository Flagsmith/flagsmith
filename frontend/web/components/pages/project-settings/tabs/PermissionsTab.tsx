import EditPermissions from 'components/EditPermissions'
import React from 'react'
import { useGetRolesQuery } from 'common/services/useRole'
import { useGetProjectPermissionsQuery } from 'common/services/useProject'
import { ProjectSettingsTabProps } from 'components/pages/project-settings/shared/types'

export const PermissionsTab = ({
  organisationId,
  projectId,
}: ProjectSettingsTabProps) => {
  const { data: rolesData } = useGetRolesQuery(
    { organisation_id: organisationId || 0 },
    { skip: !organisationId },
  )

  const { data: permissionsData, refetch: refetchPermissions } =
    useGetProjectPermissionsQuery({ projectId: String(projectId) })

  const handleSaveUser = () => {
    refetchPermissions()
  }

  return (
    <EditPermissions
      tabClassName='flat-panel'
      id={projectId}
      level='project'
      roleTabTitle='Project Permissions'
      roles={rolesData?.results || []}
      permissions={permissionsData?.results || []}
      onSaveUser={handleSaveUser}
    />
  )
}
