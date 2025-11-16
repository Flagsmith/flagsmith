import React, { FC, useEffect } from 'react'
import { useHasFeatureStateChanges } from 'common/hooks/useHasFeatureStateChanges'
import Checkbox from './base/forms/Checkbox'
import { ChangeSet, FeatureState } from 'common/types/responses'
import WarningMessage from './WarningMessage'
import Format from 'common/utils/format'

interface ChangeRequestConflictCheckProps {
  action: 'create' | 'publish'
  projectId: string | number
  environmentId: number
  featureId?: number
  featureStates?: FeatureState[]
  changeSets?: ChangeSet[]
  ignoreConflicts: boolean
  onIgnoreConflictsChange: (value: boolean) => void
  onHasChangesChange?: (hasChanges: boolean) => void
}

const ChangeRequestConflictCheck: FC<ChangeRequestConflictCheckProps> = ({
  action,
  changeSets,
  environmentId,
  featureId,
  featureStates,
  ignoreConflicts,
  onHasChangesChange,
  onIgnoreConflictsChange,
  projectId,
}) => {
  const hasChanges = useHasFeatureStateChanges({
    changeSets,
    environmentId,
    featureId,
    featureStates,
    projectId,
  })

  useEffect(() => {
    onHasChangesChange?.(hasChanges)
  }, [hasChanges, onHasChangesChange])

  if (!hasChanges) {
    return (
      <div>
        <WarningMessage
          warningMessage={'This change request has no changes.'}
        />
        <Checkbox
          label={`${Format.camelCase(
            action,
          )} this change request even though there are no changes to the feature?`}
          checked={ignoreConflicts}
          onChange={onIgnoreConflictsChange}
        />
      </div>
    )
  }

  return null
}

export default ChangeRequestConflictCheck
