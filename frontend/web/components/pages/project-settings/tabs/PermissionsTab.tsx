import EditPermissions from 'components/EditPermissions'
import InfoMessage from 'components/InfoMessage'
import React from 'react'
import { useGetRolesQuery } from 'common/services/useRole'
import { useGetProjectPermissionsQuery } from 'common/services/useProject'

type PermissionsTabProps = {
  projectId: number
  organisationId: number
}

export const PermissionsTab = ({
  organisationId,
  projectId,
}: PermissionsTabProps) => {
  const {
    data: rolesData,
    error: rolesError,
    isLoading: rolesLoading,
  } = useGetRolesQuery({ organisation_id: organisationId })

  const {
    data: permissionsData,
    error: permissionsError,
    isLoading: permissionsLoading,
    refetch: refetchPermissions,
  } = useGetProjectPermissionsQuery({ projectId: String(projectId) })

  const handleSaveUser = () => {
    refetchPermissions()
  }

  if (rolesLoading || permissionsLoading) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }

  if (rolesError || permissionsError) {
    return (
      <div className='mt-4'>
        <InfoMessage>Error loading permissions data</InfoMessage>
      </div>
    )
  }

  return (
    <EditPermissions
      tabClassName='flat-panel'
      id={projectId}
      level='project'
      roleTabTitle='Project Permissions'
      roles={rolesData?.results || []}
      permissions={permissionsData || []}
      onSaveUser={handleSaveUser}
    />
  )
}
