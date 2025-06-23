import { FC } from 'react'
import InfoMessage from './InfoMessage'
import { useHistory } from 'react-router-dom'
import Button from './base/forms/Button'
import { ChangeRequestSummary } from 'common/types/responses'

type ExistingChangeRequestAlertType = {
  changeRequests: ChangeRequestSummary[]
  editingChangeRequest?: ChangeRequestSummary
  scheduledChangeRequests: ChangeRequestSummary[]
  projectId: number | string
  environmentId: string
  className?: string
}

const ExistingChangeRequestAlert: FC<ExistingChangeRequestAlertType> = ({
  changeRequests,
  className,
  editingChangeRequest,
  environmentId,
  projectId,
  scheduledChangeRequests,
}) => {
  const history = useHistory()

  const handleNavigate = () => {
    const changes = scheduledChangeRequests?.length
      ? scheduledChangeRequests
      : changeRequests
    const latestChangeRequest = !editingChangeRequest?.id
      ? changes?.at(-1)?.id
      : editingChangeRequest?.id
    closeModal()
    history.push(
      `/project/${projectId}/environment/${environmentId}/change-requests/${latestChangeRequest}`,
    )
  }

  const getRequestChangeInfoText = (
    hasScheduledChangeRequests: boolean,
    hasChangeRequests: boolean,
  ) => {
    if (hasScheduledChangeRequests) {
      return [
        'You have scheduled changes upcoming for this feature.',
        'to view your scheduled changes.',
      ]
    }

    if (hasChangeRequests) {
      return [
        'You have open change requests for this feature.',
        'to view your requested changes.',
      ]
    }
  }

  const requestChangeInfoText = getRequestChangeInfoText(
    !!scheduledChangeRequests?.length,
    !!changeRequests?.length,
  )

  if (!requestChangeInfoText?.length) {
    return null
  }

  return (
    <div className={className}>
      <InfoMessage>
        <span>
          {requestChangeInfoText[0]} Click{' '}
          <Button onClick={handleNavigate} theme='text'>
            here
          </Button>{' '}
          {requestChangeInfoText[1]}
        </span>
      </InfoMessage>
    </div>
  )
}

export default ExistingChangeRequestAlert
