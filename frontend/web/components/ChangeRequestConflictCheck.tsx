import React, { FC, useEffect, useMemo } from 'react'
import { useHasFeatureStateChanges } from 'common/hooks/useHasFeatureStateChanges'
import Checkbox from './base/forms/Checkbox'
import { ChangeSet, FeatureState } from 'common/types/responses'
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
  liveFrom?: string | null
  ignoreConflicts: boolean
  onIgnoreConflictsChange: (value: boolean) => void
  onHasChangesChange?: (hasChanges: boolean) => void
  onHasWarningChange?: (hasWarning: boolean) => void
}

/**
 * ChangeRequestConflictCheck displays a warning when:
 * - Creating a change request with no feature state changes
 * - Publishing a change request that is scheduled in the future
 */
const ChangeRequestConflictCheck: FC<ChangeRequestConflictCheckProps> = ({
  action,
  changeSets,
  environmentId,
  featureId,
  featureStates,
  ignoreConflicts,
  liveFrom,
  onHasChangesChange,
  onHasWarningChange,
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

  const isScheduledInFuture = useMemo(() => {
    return liveFrom ? moment(liveFrom).isAfter(moment()) : false
  }, [liveFrom])

  const hasWarning = useMemo(() => {
    return (
      (!hasChanges && action === 'create') ||
      (isScheduledInFuture && action === 'publish')
    )
  }, [hasChanges, action, isScheduledInFuture])

  useEffect(() => {
    onHasWarningChange?.(hasWarning)
  }, [hasWarning, onHasWarningChange])

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

  if (isScheduledInFuture && action === 'publish') {
    return (
      <div>
        <WarningMessage
          warningMessage={
            'By choosing to ignore conflicts, the change defined in this Change Request will become live regardless of any changes that happen to this feature between now and the scheduled live date. This may result in a loss of those changes, please proceed with care.'
          }
        />
        <Checkbox
          label='Publish this change request anyway, ignoring conflicts'
          checked={ignoreConflicts}
          onChange={onIgnoreConflictsChange}
        />
      </div>
    )
  }

  return null
}

export default ChangeRequestConflictCheck
