import React, { FC, useEffect, useMemo } from 'react'
import { useHasFeatureStateChanges } from 'common/hooks/useHasFeatureStateChanges'
import Checkbox from './base/forms/Checkbox'
import {
  ChangeSet,
  FeatureConflict,
  FeatureState,
} from 'common/types/responses'
import WarningMessage from './WarningMessage'
import Format from 'common/utils/format'
import moment from 'moment'

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
  liveFrom?: string
  conflicts?: FeatureConflict[]
}

/**
 * ChangeRequestConflictCheck displays warnings and allows users to bypass them:
 *
 * 1. No Changes Warning: Shown when creating a change request and no feature state changes are detected
 * 2. Publish Conflict Warning: Shown when action is 'publish' AND either:
 *    - The change request has conflicts (changeRequest.conflicts has items), OR
 *    - The scheduled date (liveFrom) is set to a future date
 */
const ChangeRequestConflictCheck: FC<ChangeRequestConflictCheckProps> = ({
  action,
  changeSets,
  conflicts,
  environmentId,
  featureId,
  featureStates,
  ignoreConflicts,
  liveFrom,
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

  const isScheduledInFuture = useMemo(() => {
    return liveFrom ? moment(liveFrom).isAfter(moment()) : false
  }, [liveFrom])

  const hasConflicts = useMemo(() => {
    return conflicts && conflicts.length > 0
  }, [conflicts])

  useEffect(() => {
    onHasChangesChange?.(hasChanges)
  }, [hasChanges, onHasChangesChange])

  const shouldShowPublishWarning =
    action === 'publish' && (hasConflicts || isScheduledInFuture)

  if (!hasChanges && action === 'create') {
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

  if (shouldShowPublishWarning) {
    return (
      <div>
        <WarningMessage
          warningMessage={
            'By choosing to ignore conflicts, the change defined in this Change Request will become live regardless of any changes that happen to this feature between now and the scheduled live date. This may result in a loss of those changes, please proceed with care.'
          }
        />
        <Checkbox
          label='Ignore conflicts and publish anyway'
          checked={ignoreConflicts}
          onChange={onIgnoreConflictsChange}
        />
      </div>
    )
  }

  return null
}

export default ChangeRequestConflictCheck
