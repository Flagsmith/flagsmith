import React, { FC, useState } from 'react'
import { useGetUsersQuery } from 'common/services/useUser'
import { useGetGroupSummariesQuery } from 'common/services/useGroupSummary'
import AccountStore from 'common/stores/account-store'
import UserSelect from './UserSelect'
import GroupSelect from './GroupSelect'
import { IonIcon } from '@ionic/react'
import { close } from 'ionicons/icons'
import getUserDisplayName from 'common/utils/getUserDisplayName'
import PlanBasedBanner from './PlanBasedAccess'
import Utils from 'common/utils/utils'

type FeatureOwnerSelectProps = {
  selectedUserIds: number[]
  selectedGroupIds: number[]
  onUserIdsChange: (ids: number[]) => void
  onGroupIdsChange: (ids: number[]) => void
}

const FeatureOwnerSelect: FC<FeatureOwnerSelectProps> = ({
  onGroupIdsChange,
  onUserIdsChange,
  selectedGroupIds,
  selectedUserIds,
}) => {
  const [showUsers, setShowUsers] = useState(false)
  const [showGroups, setShowGroups] = useState(false)

  const organisationId = AccountStore.getOrganisation()?.id
  const { data: users } = useGetUsersQuery(
    { organisationId },
    { skip: !organisationId },
  )
  const { data: groups } = useGetGroupSummariesQuery(
    { orgId: organisationId },
    { skip: !organisationId },
  )

  const hasFlagOwnersPlan = Utils.getPlansPermission('FLAG_OWNERS')

  if (!hasFlagOwnersPlan) {
    return (
      <PlanBasedBanner
        className='mb-3'
        feature={'FLAG_OWNERS'}
        theme={'description'}
      />
    )
  }

  const selectedUsers =
    users?.filter((u) => selectedUserIds.includes(u.id)) ?? []
  const selectedGroups =
    groups?.filter((g) => selectedGroupIds.includes(g.id)) ?? []

  const handleAddUser = (id: number) => {
    if (!selectedUserIds.includes(id)) {
      onUserIdsChange([...selectedUserIds, id])
    }
  }

  const handleRemoveUser = (id: number) => {
    onUserIdsChange(selectedUserIds.filter((uid) => uid !== id))
  }

  const handleAddGroup = (id: number) => {
    if (!selectedGroupIds.includes(id)) {
      onGroupIdsChange([...selectedGroupIds, id])
    }
  }

  const handleRemoveGroup = (id: number) => {
    onGroupIdsChange(selectedGroupIds.filter((gid) => gid !== id))
  }

  return (
    <div>
      <div className='mb-3'>
        <Row className='gap-2 align-items-center mb-2'>
          <label
            className='cols-sm-2 control-label mb-0 cursor-pointer hover-color-primary'
            onClick={() => setShowUsers(!showUsers)}
          >
            Assigned users
          </label>
        </Row>
        <Row style={{ rowGap: '12px' }}>
          {selectedUsers.map((u) => (
            <Row
              key={u.id}
              onClick={() => handleRemoveUser(u.id)}
              className='chip mr-2'
            >
              <span className='font-weight-bold'>{getUserDisplayName(u)}</span>
              <span className='chip-icon ion'>
                <IonIcon icon={close} />
              </span>
            </Row>
          ))}
          {!selectedUsers.length && (
            <div className='text-muted fs-small'>No users assigned</div>
          )}
        </Row>
        <UserSelect
          disabled={false}
          users={users ?? []}
          value={selectedUserIds}
          onAdd={handleAddUser}
          onRemove={handleRemoveUser}
          isOpen={showUsers}
          onToggle={() => setShowUsers(!showUsers)}
        />
      </div>

      <div className='mb-3'>
        <Row className='gap-2 align-items-center mb-2'>
          <label
            className='cols-sm-2 control-label mb-0 cursor-pointer hover-color-primary'
            onClick={() => setShowGroups(!showGroups)}
          >
            Assigned groups
          </label>
        </Row>
        <Row style={{ rowGap: '12px' }}>
          {selectedGroups.map((g) => (
            <Row
              key={g.id}
              onClick={() => handleRemoveGroup(g.id)}
              className='chip mr-2'
            >
              <span className='font-weight-bold'>{g.name}</span>
              <span className='chip-icon ion'>
                <IonIcon icon={close} />
              </span>
            </Row>
          ))}
          {!selectedGroups.length && (
            <div className='text-muted fs-small'>No groups assigned</div>
          )}
        </Row>
        <GroupSelect
          groups={groups}
          value={selectedGroupIds}
          onAdd={handleAddGroup}
          onRemove={handleRemoveGroup}
          isOpen={showGroups}
          onToggle={() => setShowGroups(!showGroups)}
        />
      </div>
    </div>
  )
}

export default FeatureOwnerSelect
