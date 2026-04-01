import React, { FC, useEffect, useState } from 'react'
import _data from 'common/data/base/_data'
import UserSelect from './UserSelect'
import { IonIcon } from '@ionic/react'
import { close } from 'ionicons/icons'
import { getProjectFlag } from 'common/services/useProjectFlag'
import { getStore } from 'common/store'
import SettingsButton from './SettingsButton'
import { useGetUsersQuery } from 'common/services/useUser'
import AccountStore from 'common/stores/account-store'
import Project from 'common/project'

type FlagOwnersEditProps = {
  projectId: number | string
  id: number
  selectedIds?: never
  onAdd?: never
  onRemove?: never
}

type FlagOwnersCreateProps = {
  projectId?: never
  id?: never
  selectedIds: number[]
  onAdd: (id: number) => void
  onRemove: (id: number) => void
}

type FlagOwnersProps = FlagOwnersEditProps | FlagOwnersCreateProps

const FlagOwners: FC<FlagOwnersProps> = (props) => {
  const [showUsers, setShowUsers] = useState(false)
  const [internalOwners, setInternalOwners] = useState<number[]>([])

  const organisationId = AccountStore.getOrganisation()?.id
  const { data: users } = useGetUsersQuery(
    { organisationId },
    { skip: !organisationId },
  )

  useEffect(() => {
    if (props.id) {
      getProjectFlag(getStore(), {
        id: props.id,
        project:
          typeof props.projectId === 'string'
            ? parseInt(props.projectId, 10)
            : props.projectId,
      }).then((res) => {
        const ownerIds = (res.data.owners || []).map(
          (v: { id: number }) => v.id,
        )
        setInternalOwners(ownerIds)
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const owners = props.id ? internalOwners : props.selectedIds ?? []

  const addOwner = (id: number) => {
    if (props.id) {
      setInternalOwners((prev) => prev.concat(id))
      _data.post(
        `${Project.api}projects/${props.projectId}/features/${props.id}/add-owners/`,
        { user_ids: [id] },
      )
    } else if (props.onAdd) {
      props.onAdd(id)
    }
  }

  const removeOwner = (id: number) => {
    if (props.id) {
      setInternalOwners((prev) => prev.filter((v) => v !== id))
      _data.post(
        `${Project.api}projects/${props.projectId}/features/${props.id}/remove-owners/`,
        { user_ids: [id] },
      )
    } else if (props.onRemove) {
      props.onRemove(id)
    }
  }

  const ownerUsers = users ? users.filter((v) => owners.includes(v.id)) : []

  const getUserLabel = (user: {
    first_name: string
    last_name: string
    email: string
  }) => {
    if (user.first_name || user.last_name) {
      return `${user.first_name} ${user.last_name}`
    }
    return user.email || 'Unknown'
  }

  return (
    <div>
      <SettingsButton
        content={
          <Row style={{ rowGap: '12px' }}>
            {ownerUsers.map((u) => (
              <Row
                key={u.id}
                onClick={() => removeOwner(u.id)}
                className='chip mr-2'
              >
                <span className='font-weight-bold'>{getUserLabel(u)}</span>
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
        value={owners}
        onAdd={addOwner as unknown as (id: string) => void}
        onRemove={removeOwner as unknown as (id: string) => void}
        isOpen={showUsers}
        onToggle={() => setShowUsers(!showUsers)}
      />
    </div>
  )
}

export default FlagOwners
