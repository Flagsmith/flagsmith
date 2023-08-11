import React, { FC, useEffect, useState } from 'react'
import InputGroup from 'components/base/forms/InputGroup'
import Tabs from 'components/base/forms/Tabs'
import TabItem from 'components/base/forms/TabItem'
import PanelSearch from 'components/PanelSearch'
import { AvailablePermission } from 'common/types/responses'
import CollapsibleNestedList from 'components/CollapsibleNestedList'

type CreateRoleType = {}
const CreateRole: FC<CreateRoleType> = ({}) => {
  const [tab, setTab] = useState<number>(0)
  const [roleName, setRoleName] = useState<string>('')
  const [roleDesc, setRoleDesc] = useState<string>('')
  const isSaving = false
  const projectData = [
    {
      title: 'Project 1',
      subItems: [
        { title: 'permission 1-1' },
        { title: 'permission 1-2' },
        { title: 'Permission 1-3' },
      ],
    },
    {
      title: 'Project 2',
      subItems: [
        { title: 'permission 2-1' },
        { title: 'permission 2-2' },
        { title: 'permission 2-3' },
      ],
    },
  ];

  const envData = [
    {
      title: 'Env 1',
      subItems: [
        { title: 'permission 1-1' },
        { title: 'permission 1-2' },
        { title: 'Permission 1-3' },
      ],
    },
    {
      title: 'Env 2',
      subItems: [
        { title: 'permission 2-1' },
      ],
    },
  ];


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

  const TabValue = () => {
    return (
      <Tabs value={tab} onChange={setTab}>
        <TabItem tabLabel='Rol'>
          <div className='my-4'>
            <p>Edit Permissions</p>
            <InputGroup
              title='Role name'
              inputProps={{
                className: 'full-width',
                name: 'roleName',
              }}
              value={roleName}
              onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
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
              onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
                setRoleDesc(Utils.safeParseEventValue(event))
              }}
              id='description'
              placeholder='E.g. Some role description'
            />
            <div className='text-right mb-2'>
              <Button
                onClick={() => console.log('DEBUG save')}
                data-test='update-role-btn'
                id='update-role-btn'
                //   disabled={isSaving || !name || invalid}
              >
                {isSaving ? 'Updating' : 'Update Role'}
              </Button>
            </div>
          </div>
        </TabItem>
        <TabItem tabLabel='Organisation permission'>
          <PanelSearch
            title='Edit Permissions'
            className='no-pad my-4'
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
          />
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
    )
  }

  return (
    <div id='create-feature-modal'>
      <TabValue />
    </div>
  )
}

export default CreateRole

module.exports = CreateRole
