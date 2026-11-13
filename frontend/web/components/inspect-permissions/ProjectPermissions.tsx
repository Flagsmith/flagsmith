import React, { useState } from 'react'
import PanelSearch from 'components/PanelSearch'

import Utils from 'common/utils/utils'

import { useGetProjectsQuery } from 'common/services/useProject'
import EmptyState from 'components/EmptyState'
import Button from 'components/base/forms/Button'
import Input from 'components/base/forms/Input'
import ExpandablePermissionsList from './ExpandablePermissionsList'

type ProjectPermissionsProps = {
  organisationId: number
  userId?: number
}

const ProjectPermissions = ({
  organisationId,
  userId,
}: ProjectPermissionsProps) => {
  const {
    data: projects,
    isError,
    isLoading,
    refetch,
  } = useGetProjectsQuery({ organisationId })
  const [searchProject, setSearchProject] = useState<string>('')
  const filteredProjects = projects?.filter((v) => {
    const search = searchProject?.toLowerCase()
    if (!search) return true
    return `${v.name}`.toLowerCase().includes(search)
  })
  return (
    <>
      <Row className='justify-content-between'>
        <h5 className='my-3'>Permissions</h5>
        <Input
          type='text'
          className='ml-3='
          value={searchProject}
          onChange={(e) => {
            setSearchProject(Utils.safeParseEventValue(e))
          }}
          size='small'
          placeholder='Search Projects'
          search
        />
      </Row>
      {isError && !projects && (
        <EmptyState
          status='error'
          title='Could not load projects'
          description='Try again in a few moments.'
          action={
            <Button theme='outline' size='small' onClick={() => refetch()}>
              Try again
            </Button>
          }
        />
      )}
      <PanelSearch
        isLoading={isLoading}
        header={
          <Row className='table-header'>
            <Flex className='px-3'>Name</Flex>
          </Row>
        }
        className='no-pad'
        items={filteredProjects}
        renderRow={(project) => (
          <ExpandablePermissionsList
            key={project.id}
            item={project}
            level='project'
            userId={userId}
            projectId={project.id}
            getItemName={(project) => project.name}
            getItemId={(project) => project.id}
            getLevelId={(project) => String(project.id)}
          />
        )}
      />
    </>
  )
}

export default ProjectPermissions
