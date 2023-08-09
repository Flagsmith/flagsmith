import React, { FC, useEffect, useState } from 'react'
import InputGroup from 'components/base/forms/InputGroup'
import Tabs from 'components/base/forms/Tabs'
import TabItem from 'components/base/forms/TabItem'
import PanelSearch from 'components/PanelSearch'

type CreateRoleType = {}
const CreateRole: FC<CreateRoleType> = ({}) => {
  const [tab, setTab] = useState<number>(0)
  const [roleName, setRoleName] = useState<string>('')
  const [roleDesc, setRoleDesc] = useState<string>('')
  const isSaving = false

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
          title='Permissions'
          className='no-pad mb-4'
          items={permissions}

        />
        </TabItem>
        <TabItem tabLabel='Project permission'>
          <div className='my-4' />
        </TabItem>
        <TabItem tabLabel='Environment permission'>
          <div className='my-4' />
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
