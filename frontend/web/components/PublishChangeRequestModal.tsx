import React, { FC, ReactNode, useState } from 'react'
import { ChangeRequest, ProjectChangeRequest } from 'common/types/responses'
import ChangeRequestConflictCheck from './ChangeRequestConflictCheck'
import { getChangeRequestLiveDate } from 'common/utils/getChangeRequestLiveDate'

interface PublishChangeRequestContentProps {
  changeRequest: ChangeRequest
  projectId: string
  environmentId: number
  isScheduled?: boolean
  scheduledDate?: string
  children?: ReactNode
  onIgnoreConflictsChange?: (ignoreConflicts: boolean) => void
  onHasWarningDetected?: (hasWarning: boolean) => void
}

export const PublishChangeRequestContent: FC<
  PublishChangeRequestContentProps
> = ({
  changeRequest,
  children,
  environmentId,
  isScheduled,
  onHasWarningDetected,
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

  const handleHasWarningChange = (hasWarning: boolean) => {
    onHasWarningDetected?.(hasWarning)
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
        liveFrom={getChangeRequestLiveDate(changeRequest)?.toISOString()}
        ignoreConflicts={ignoreConflicts}
        onIgnoreConflictsChange={handleIgnoreConflictsChange}
        onHasWarningChange={handleHasWarningChange}
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
  let hasWarning = false

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
        onHasWarningDetected={(value) => {
          hasWarning = value
        }}
      >
        {children}
      </PublishChangeRequestContent>
    ),
    onYes: () => {
      onYes(hasWarning ? ignoreConflicts : undefined)
    },
    title: 'Publish Change Request',
  })
}
