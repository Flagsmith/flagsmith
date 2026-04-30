import { FC, useState } from 'react'
import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'
import PermissionsTabs from 'components/PermissionsTabs'
import UsersGroups from 'components/UsersGroups'
import { User } from 'common/types/responses'

type EditUserPermissionsModalProps = {
  user: User
  orgId: number
}

const EditUserPermissionsModal: FC<EditUserPermissionsModalProps> = ({
  orgId,
  user,
}) => {
  const [tab, setTab] = useState(0)
  return (
    <div>
      <Tabs
        value={tab}
        onChange={setTab}
        hideNavOnSingleTab
        className='mt-4 ml-3'
      >
        {user.role !== 'ADMIN' && (
          <TabItem tabLabel='Permissions'>
            <div className='pt-4'>
              <PermissionsTabs uncontrolled user={user} orgId={orgId} />
            </div>
          </TabItem>
        )}
        <TabItem tabLabel='Groups'>
          <div className='pt-4'>
            <UsersGroups user={user} orgId={orgId} />
          </div>
        </TabItem>
      </Tabs>
    </div>
  )
}

export default EditUserPermissionsModal
