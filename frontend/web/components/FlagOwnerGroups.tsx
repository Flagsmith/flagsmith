import React, { FC, useState } from 'react'
import ConnectedGroupSelect from './ConnectedGroupSelect'
import SettingsButton from './SettingsButton'
import { useCurrentOrganisation } from 'common/hooks/useCurrentOrganisation'

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
  const organisation = useCurrentOrganisation()
  const [showGroups, setShowGroups] = useState(false)

  return (
    <div>
      <SettingsButton
        feature='FLAG_OWNERS'
        content={
          organisation && (
            <ConnectedGroupSelect
              orgId={`${organisation.id}`}
              showValues
              groups={undefined}
              value={selectedIds}
              isOpen={showGroups}
              onAdd={(id: number) => onAdd(id)}
              onRemove={(id: number) => onRemove(id)}
              onToggle={() => setShowGroups(!showGroups)}
            />
          )
        }
        onClick={() => setShowGroups(true)}
      >
        Assigned groups
      </SettingsButton>
    </div>
  )
}

export default FlagOwnerGroups
