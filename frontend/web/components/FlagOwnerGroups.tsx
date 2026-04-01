import React, { FC, useEffect, useState } from 'react'
import _data from 'common/data/base/_data'
import { getProjectFlag } from 'common/services/useProjectFlag'
import { getStore } from 'common/store'
import ConnectedGroupSelect from './ConnectedGroupSelect'
import SettingsButton from './SettingsButton'
import AccountStore from 'common/stores/account-store'
import Project from 'common/project'

type FlagOwnerGroupsEditProps = {
  projectId: number | string
  id: number
  selectedIds?: never
  onAdd?: never
  onRemove?: never
}

type FlagOwnerGroupsCreateProps = {
  projectId?: never
  id?: never
  selectedIds: number[]
  onAdd: (id: number) => void
  onRemove: (id: number) => void
}

type FlagOwnerGroupsProps =
  | FlagOwnerGroupsEditProps
  | FlagOwnerGroupsCreateProps

const FlagOwnerGroups: FC<FlagOwnerGroupsProps> = (props) => {
  const [showGroups, setShowGroups] = useState(false)
  const [internalGroupOwners, setInternalGroupOwners] = useState<number[]>([])

  useEffect(() => {
    if (props.id) {
      getProjectFlag(getStore(), {
        id: props.id,
        project:
          typeof props.projectId === 'string'
            ? parseInt(props.projectId, 10)
            : props.projectId,
      }).then((res) => {
        const groupIds = (res.data.group_owners || []).map(
          (v: { id: number }) => v.id,
        )
        setInternalGroupOwners(groupIds)
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const groupOwners = props.id ? internalGroupOwners : props.selectedIds ?? []

  const addOwner = (id: number) => {
    if (props.id) {
      setInternalGroupOwners((prev) => prev.concat(id))
      _data.post(
        `${Project.api}projects/${props.projectId}/features/${props.id}/add-group-owners/`,
        { group_ids: [id] },
      )
    } else if (props.onAdd) {
      props.onAdd(id)
    }
  }

  const removeOwner = (id: number) => {
    if (props.id) {
      setInternalGroupOwners((prev) => prev.filter((v) => v !== id))
      _data.post(
        `${Project.api}projects/${props.projectId}/features/${props.id}/remove-group-owners/`,
        { group_ids: [id] },
      )
    } else if (props.onRemove) {
      props.onRemove(id)
    }
  }

  return (
    <div>
      <SettingsButton
        feature='FLAG_OWNERS'
        content={
          <ConnectedGroupSelect
            orgId={AccountStore.getOrganisation()?.id}
            showValues
            groups={undefined}
            value={groupOwners}
            isOpen={showGroups}
            onAdd={(id: number) => addOwner(id)}
            onRemove={(id: number) => removeOwner(id)}
            onToggle={() => setShowGroups(!showGroups)}
          />
        }
        onClick={() => setShowGroups(true)}
      >
        Assigned groups
      </SettingsButton>
    </div>
  )
}

export default FlagOwnerGroups
