import React, { FC, useEffect, useState } from 'react'
import InputGroup from 'components/base/forms/InputGroup'
import Tabs from 'components/base/forms/Tabs'
import TabItem from 'components/base/forms/TabItem'
import PanelSearch from 'components/PanelSearch'
import { AvailablePermission } from 'common/types/responses'
import CollapsibleNestedList from 'components/CollapsibleNestedList'
import {
  useGetRoleQuery,
  useCreateRoleMutation,
  useUpdateRoleMutation,
} from 'common/services/useRole'

import EditPermissions from 'components/EditPermissions'


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
  console.log('DEBUG role:', role)
  const buttonText = isEdit ? 'Update Role' : 'Create Role'
  const [tab, setTab] = useState<number>(0)
  const isSaving = false
  const projectData = [
    {
      subItems: [
        { title: 'permission 1-1' },
        { title: 'permission 1-2' },
        { title: 'Permission 1-3' },
      ],
      title: 'Project 1',
    },
    {
      subItems: [
        { title: 'permission 2-1' },
        { title: 'permission 2-2' },
        { title: 'permission 2-3' },
      ],
      title: 'Project 2',
    },
  ]

  const envData = [
    {
      subItems: [
        { title: 'permission 1-1' },
        { title: 'permission 1-2' },
        { title: 'Permission 1-3' },
      ],
      title: 'Env 1',
    },
    {
      subItems: [{ title: 'permission 2-1' }],
      title: 'Env 2',
    },
  ]

  const orgPerm = [
    {
      'description': 'Allows the user to create projects in this organisation.',
      'key': 'CREATE_PROJECT',
    },
    {
      'description': 'Allows the user to invite users to the organisation.',
      'key': 'MANAGE_USERS',
    },
    {
      'description':
        'Allows the user to manage the groups in the organisation and their members.',
      'key': 'MANAGE_USER_GROUPS',
    },
  ]

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
      console.log('DEBUG: isEdit:', isEdit)
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
        <TabItem tabLabel='Organisation permission'>
        <EditPermissions
            tabClassName='flat-panel'
            parentId='test-idpar'
            parentLevel='project'
            parentSettingsLink={`/project/test-id/settings`}
            id='test-id'
            level='environment'
          />
          {/* <PanelSearch
            title='Edit Permissions'
            className='no-pad my-2'
            items={orgPerm}
            renderRow={(p: AvailablePermission) => {
              return (
                <Row
                  key={p.key}
                  style={{ opacity: 1 }}
                  className='list-item list-item-sm px-3'
                >
                  <Row space>
                    <Flex>
                      <div className='list-item-subtitle'>{p.description}</div>
                    </Flex>
                    <Switch
                      onChange={() => console.log('DEBUG swicht')}
                      disabled={false}
                      checked={true}
                    />
                  </Row>
                </Row>
              )
            }}
          /> */}
          <div className='text-right mb-2'>
            <Button
              onClick={() => console.log('DEBUG save')}
              data-test='update-role-btn'
              id='update-role-btn'
              //   disabled={isSaving || !name || invalid}
            >
              {isSaving ? 'Updating' : 'Update Permissions'}
            </Button>
          </div>
        </TabItem>
        <TabItem tabLabel='Project permission'>
          <h5 className='my-4 title'>Edit Permissions</h5>
          <CollapsibleNestedList mainItems={projectData} isButtonVisible />
          <div className='text-right mb-2'>
            <Button
              onClick={() => console.log('DEBUG save')}
              data-test='update-role-btn'
              id='update-role-btn'
              //   disabled={isSaving || !name || invalid}
            >
              {isSaving ? 'Updating' : 'Update Permissions'}
            </Button>
          </div>
        </TabItem>
        <TabItem tabLabel='Environment permission'>
          <h5 className='my-4 title'>Edit Permissions</h5>
          <CollapsibleNestedList mainItems={envData} />
          <div className='text-right mb-2'>
            <Button
              onClick={() => console.log('DEBUG save')}
              data-test='update-role-btn'
              id='update-role-btn'
              //   disabled={isSaving || !name || invalid}
            >
              {isSaving ? 'Updating' : 'Update Permissions'}
            </Button>
          </div>
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
