import React, { FC, useEffect, useState } from 'react'
import InputGroup from 'components/base/forms/InputGroup'
import Tabs from 'components/base/forms/Tabs'
import TabItem from 'components/base/forms/TabItem'
import CollapsibleNestedList from 'components/CollapsibleNestedList'
import {
  useGetRoleQuery,
  useCreateRoleMutation,
  useUpdateRoleMutation,
} from 'common/services/useRole'

import { EditPermissionsModal } from 'components/EditPermissions'
import OrganisationStore from 'common/stores/organisation-store'
import ProjectFilter from 'components/ProjectFilter'
import { Environment } from 'common/types/responses'

type CreateRoleType = {
  organisationId?: string
  role: Role
  onComplete: () => void
  isEdit?: boolean
}
const CreateRole: FC<CreateRoleType> = ({
  isEdit,
  onComplete,
  organisationId,
  role,
}) => {
  const buttonText = isEdit ? 'Update Role' : 'Create Role'
  const [tab, setTab] = useState<number>(0)
  const [project, setProject] = useState<string>('')
  const [environments, setEnvironments] = useState<Environment[]>([])

  const isSaving = false
  const projectData = OrganisationStore.getProjects()

  useEffect(() => {
    if (project) {
      const environments = projectData.find(
        (p) => p.id === parseInt(project),
      ).environments
      setEnvironments(environments)
    }
  }, [project, projectData])

  const selectProject = (project) => {
    console.log('DEBUG: selectProject:', project, 'tab:', tab)
    setProject(project)
    setTab(3)
  }
  const Tab1 = () => {
    const { data: roleData, isLoading } = useGetRoleQuery(
      {
        organisation_id: role?.organisation,
        role_id: role?.id,
      },
      { skip: !role },
    )
    const [roleName, setRoleName] = useState<string>('')
    const [roleDesc, setRoleDesc] = useState<string>('')

    useEffect(() => {
      if (!isLoading && isEdit && roleData) {
        setRoleName(roleData.name)
      }
    }, [roleData, isLoading])

    const [
      createRole,
      { isError: createError, isLoading: creating, isSuccess: createSuccess },
    ] = useCreateRoleMutation()

    const [
      editRole,
      { isError: updateError, isLoading: updating, isSuccess: updateSuccess },
    ] = useUpdateRoleMutation()

    useEffect(() => {
      if (createSuccess || updateSuccess) {
        onComplete?.()
      }
    }, [createSuccess, updateSuccess])

    const save = () => {
      if (isEdit) {
        editRole({
          body: { name: roleName },
          organisation_id: role.organisation,
          role_id: role.id,
        })
      } else {
        createRole({
          name: roleName,
          organisation_id: organisationId,
        })
      }
    }

    return isLoading ? (
      <div className='text-center'>
        <Loader />
      </div>
    ) : (
      <div className='my-4'>
        <InputGroup
          title='Role name'
          inputProps={{
            className: 'full-width',
            name: 'roleName',
          }}
          value={roleName}
          onChange={(event) => {
            setRoleName(Utils.safeParseEventValue(event))
          }}
          id='roleName'
          placeholder='E.g. Viewers'
        />
        <InputGroup
          title='Role Description'
          inputProps={{
            className: 'full-width',
            name: 'description',
          }}
          value={roleDesc}
          onChange={(event) => {
            setRoleDesc(Utils.safeParseEventValue(event))
          }}
          id='description'
          placeholder='E.g. Some role description'
        />
        <div className='text-right mb-2'>
          <Button
            onClick={() => save()}
            data-test='update-role-btn'
            id='update-role-btn'
            disabled={isSaving || !roleName}
          >
            {isSaving && isEdit
              ? 'Updating'
              : isSaving && !isEdit
              ? 'Creating'
              : buttonText}
          </Button>
        </div>
      </div>
    )
  }

  const TabValue = () => {
    return isEdit ? (
      <Tabs value={tab} onChange={setTab}>
        <TabItem tabLabel='Rol'>
          <Tab1 />
        </TabItem>
        <TabItem tabLabel='Organisation permissions'>
          <EditPermissionsModal level={'organisation'} role={role} />
        </TabItem>
        <TabItem tabLabel='Project permissions'>
          <h5 className='my-4 title'>Edit Permissions</h5>
          <CollapsibleNestedList
            mainItems={projectData}
            // isButtonVisible
            role={role}
            level={'project'}
            // selectProject={(project) => selectProject(project)}
          />
        </TabItem>
        <TabItem tabLabel='Environment permissions'>
          <h5 className='my-4 title'>Edit Permissions</h5>
          <ProjectFilter
            organisationId={role.organisation}
            onChange={setProject}
            value={project}
            className='mb-2'
          />
          {environments.length > 0 && (
            <CollapsibleNestedList
              mainItems={environments}
              role={role}
              level={'environment'}
            />
          )}
        </TabItem>
      </Tabs>
    ) : (
      <div className='my-3 mx-4'>
        <Tab1 />
      </div>
    )
  }

  return (
    <div id='create-feature-modal'>
      <TabValue isEdit={isEdit} />
    </div>
  )
}
export default CreateRole
module.exports = CreateRole
