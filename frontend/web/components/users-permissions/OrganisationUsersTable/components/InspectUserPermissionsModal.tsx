import { FC, useState } from 'react'
import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'
import InspectPermissions from 'components/inspect-permissions/InspectPermissions'
import { User } from 'common/types/responses'

type InspectUserPermissionsModalProps = {
  user: User
  orgId: number
}

const InspectUserPermissionsModal: FC<InspectUserPermissionsModalProps> = ({
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
        <TabItem tabLabel='Permissions'>
          <div className='pt-4'>
            <InspectPermissions uncontrolled user={user} orgId={orgId} />
          </div>
        </TabItem>
      </Tabs>
    </div>
  )
}

export default InspectUserPermissionsModal
