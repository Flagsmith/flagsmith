import React, { FC, ReactNode, useState } from 'react'
import { ChangeRequest, ProjectChangeRequest } from 'common/types/responses'
import ChangeRequestConflictCheck from './ChangeRequestConflictCheck'

interface PublishChangeRequestContentProps {
  changeRequest: ChangeRequest
  projectId: string
  environmentId: number
  isScheduled?: boolean
  scheduledDate?: string
  children?: ReactNode
  onIgnoreConflictsChange?: (ignoreConflicts: boolean) => void
  onHasChangesDetected?: (hasChanges: boolean) => void
}

export const PublishChangeRequestContent: FC<
  PublishChangeRequestContentProps
> = ({
  changeRequest,
  children,
  environmentId,
  isScheduled,
  onHasChangesDetected,
  onIgnoreConflictsChange,
  projectId,
  scheduledDate,
}) => {
  const [ignoreConflicts, setIgnoreConflicts] = useState(false)

  const featureStates = changeRequest.feature_states
  const featureId =
    featureStates.length > 0 ? featureStates[0].feature : undefined

  const handleIgnoreConflictsChange = (value: boolean) => {
    setIgnoreConflicts(value)
    onIgnoreConflictsChange?.(value)
  }

  const handleHasChangesChange = (hasChanges: boolean) => {
    onHasChangesDetected?.(hasChanges)
  }

  return (
    <div>
      <div className='mb-3'>
        Are you sure you want to {isScheduled ? 'schedule' : 'publish'} this
        change request
        {isScheduled && scheduledDate ? ` for ${scheduledDate}` : ''}? This will
        adjust the feature for your environment.
      </div>

      {children}

      <ChangeRequestConflictCheck
        action='publish'
        projectId={projectId}
        environmentId={environmentId}
        featureId={featureId}
        changeSets={changeRequest.change_sets}
        featureStates={featureStates}
        ignoreConflicts={ignoreConflicts}
        onIgnoreConflictsChange={handleIgnoreConflictsChange}
        onHasChangesChange={handleHasChangesChange}
        liveFrom={featureStates[0]?.live_from}
        conflicts={changeRequest.conflicts}
      />
    </div>
  )
}

interface OpenPublishChangeRequestConfirmParams {
  changeRequest: ChangeRequest | ProjectChangeRequest
  projectId: string
  environmentId: number
  isScheduled?: boolean
  scheduledDate?: string
  onYes: (ignoreConflicts: boolean | undefined) => void
  children?: ReactNode
}

export const openPublishChangeRequestConfirm = ({
  changeRequest,
  children,
  environmentId,
  isScheduled,
  onYes,
  projectId,
  scheduledDate,
}: OpenPublishChangeRequestConfirmParams) => {
  let ignoreConflicts: boolean | undefined = undefined
  let hasChangesValue = true

  openConfirm({
    body: (
      <PublishChangeRequestContent
        changeRequest={changeRequest}
        projectId={projectId}
        environmentId={environmentId}
        isScheduled={isScheduled}
        scheduledDate={scheduledDate}
        onIgnoreConflictsChange={(value) => {
          ignoreConflicts = value
        }}
        onHasChangesDetected={(hasChanges) => {
          hasChangesValue = hasChanges
        }}
      >
        {children}
      </PublishChangeRequestContent>
    ),
    onYes: () => onYes(hasChangesValue ? undefined : ignoreConflicts),
    title: 'Publish Change Request',
  })
}
