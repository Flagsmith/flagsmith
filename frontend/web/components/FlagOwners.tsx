import React, { FC, useState } from 'react'
import UserSelect from './UserSelect'
import { IonIcon } from '@ionic/react'
import { close } from 'ionicons/icons'
import SettingsButton from './SettingsButton'
import { useGetUsersQuery } from 'common/services/useUser'
import AccountStore from 'common/stores/account-store'
import getUserDisplayName from 'common/utils/getUserDisplayName'

type FlagOwnersProps = {
  selectedIds: number[]
  onAdd: (id: number) => void
  onRemove: (id: number) => void
}

const FlagOwners: FC<FlagOwnersProps> = ({ onAdd, onRemove, selectedIds }) => {
  const [showUsers, setShowUsers] = useState(false)

  const organisationId = AccountStore.getOrganisation()?.id
  const { data: users } = useGetUsersQuery(
    { organisationId },
    { skip: !organisationId },
  )

  const ownerUsers = users
    ? users.filter((v) => selectedIds.includes(v.id))
    : []

  return (
    <div>
      <SettingsButton
        content={
          <Row style={{ rowGap: '12px' }}>
            {ownerUsers.map((u) => (
              <Row
                key={u.id}
                onClick={() => onRemove(u.id)}
                className='chip mr-2'
              >
                <span className='font-weight-bold'>
                  {getUserDisplayName(u)}
                </span>
                <span className='chip-icon ion'>
                  <IonIcon icon={close} />
                </span>
              </Row>
            ))}
            {!ownerUsers.length && <div>This flag has no assigned users</div>}
          </Row>
        }
        feature={'FLAG_OWNERS'}
        onClick={() => setShowUsers(!showUsers)}
      >
        Assigned users
      </SettingsButton>

      <UserSelect
        disabled={false}
        users={users ?? []}
        value={selectedIds}
        onAdd={onAdd}
        onRemove={onRemove}
        isOpen={showUsers}
        onToggle={() => setShowUsers(!showUsers)}
      />
    </div>
  )
}

export default FlagOwners
