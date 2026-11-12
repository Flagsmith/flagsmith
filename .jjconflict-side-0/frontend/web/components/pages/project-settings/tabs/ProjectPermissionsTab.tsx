import EditPermissions from 'components/EditPermissions'
import InfoMessage from 'components/InfoMessage'
import React from 'react'
import { useGetRolesQuery } from 'common/services/useRole'
import { useGetProjectPermissionsQuery } from 'common/services/useProject'

type ProjectPermissionsTabProps = {
  projectId: number
  organisationId: number
}

export const ProjectPermissionsTab = ({
  organisationId,
  projectId,
}: ProjectPermissionsTabProps) => {
  const {
    data: rolesData,
    error: rolesError,
    isLoading: rolesLoading,
    isSuccess: rolesSuccess,
  } = useGetRolesQuery({ organisation_id: organisationId })

  const {
    data: permissionsData,
    error: permissionsError,
    isLoading: permissionsLoading,
    refetch: refetchPermissions,
  } = useGetProjectPermissionsQuery({ projectId })

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

  if (permissionsError) {
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
      isEditRolePermission={rolesSuccess && !rolesError && !rolesLoading}
    />
  )
}
