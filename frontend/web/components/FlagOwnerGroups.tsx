import React, { FC, useState } from 'react'
import ConnectedGroupSelect from './ConnectedGroupSelect'
import SettingsButton from './SettingsButton'
import AccountStore from 'common/stores/account-store'

type FlagOwnerGroupsProps = {
  selectedIds: number[]
  onAdd: (id: number) => void
  onRemove: (id: number) => void
}

const FlagOwnerGroups: FC<FlagOwnerGroupsProps> = ({
  onAdd,
  onRemove,
  selectedIds,
}) => {
  const [showGroups, setShowGroups] = useState(false)

  return (
    <div>
      <SettingsButton
        feature='FLAG_OWNERS'
        content={
          <ConnectedGroupSelect
            orgId={AccountStore.getOrganisation()?.id}
            showValues
            groups={undefined}
            value={selectedIds}
            isOpen={showGroups}
            onAdd={(id: number) => onAdd(id)}
            onRemove={(id: number) => onRemove(id)}
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
