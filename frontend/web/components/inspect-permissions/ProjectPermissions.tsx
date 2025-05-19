import React, { useState } from 'react'
import PanelSearch from 'components/PanelSearch'
import { Project } from 'common/types/responses'

import Utils from 'common/utils/utils'

import OrganisationStore from 'common/stores/organisation-store'
import Input from 'components/base/forms/Input'
import ExpandablePermissionsList from './ExpandablePermissionsList'

const ProjectPermissions = ({ userId }: { userId?: number }) => {
  const projectData: Project[] = OrganisationStore.getProjects()
  const [searchProject, setSearchProject] = useState<string>('')
  const filteredProjects =
    projectData &&
    projectData?.filter((v) => {
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
          onChange={(e: InputEvent) => {
            setSearchProject(Utils.safeParseEventValue(e))
          }}
          size='small'
          placeholder='Search Projects'
          search
        />
      </Row>
      <PanelSearch
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
