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
import { setInterceptClose } from 'components/modals/base/ModalDefault'
import {
  useGetRoleProjectPermissionsQuery
} from 'common/services/useRolePermission'

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
  const [valueChanged, setValueChanged] = useState<boolean>(false)

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

    const onClosing = () => {
      if (valueChanged) {
        return new Promise((resolve) => {
          openConfirm(
            'Are you sure?',
            'Closing this will discard your unsaved changes.',
            () => resolve(true),
            () => resolve(false),
            'Ok',
            'Cancel',
          )
        })
      } else {
        return Promise.resolve(true)
      }
    }

    useEffect(() => {
      if (isEdit && valueChanged) {
        setInterceptClose(onClosing)
      }
    }, [valueChanged])

    useEffect(() => {
      if (!isLoading && isEdit && roleData) {
        setRoleName(roleData.name)
        setRoleDesc(roleData.description)
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
        setValueChanged(false)
        onComplete?.()
      }
    }, [createSuccess, updateSuccess])

    const save = () => {
      if (isEdit) {
        editRole({
          body: { description: roleDesc, name: roleName },
          organisation_id: role.organisation,
          role_id: role.id,
        })
      } else {
        createRole({
          description: roleDesc,
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
            setValueChanged(true)
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
            setValueChanged(true)
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
        <TabItem
          tabLabel={
            <Row className='justify-content-center'>
              Role
              {valueChanged && <div className='unread ml-2 px-1'>{'*'}</div>}
            </Row>
          }
        >
          <Tab1 />
        </TabItem>
        <TabItem
          tabLabel={
            <Row className='justify-content-center'>
              Organisation permissions
            </Row>
          }
        >
          <EditPermissionsModal level={'organisation'} role={role} />
        </TabItem>
        <TabItem
          tabLabel={
            <Row className='justify-content-center'>Project permissions</Row>
          }
        >
          <h5 className='my-4 title'>Edit Permissions</h5>
          <CollapsibleNestedList
            mainItems={projectData}
            role={role}
            level={'project'}
          />
        </TabItem>
        <TabItem
          tabLabel={
            <Row className='justify-content-center'>
              Environment permissions
            </Row>
          }
        >
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
