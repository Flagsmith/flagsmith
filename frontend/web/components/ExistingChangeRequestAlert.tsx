import { FC, useRef } from 'react'
import { useGetChangeRequestsQuery } from 'common/services/useChangeRequest'
import moment from 'moment'
import InfoMessage from './InfoMessage'
import { RouterChildContext } from 'react-router-dom'
import Button from './base/forms/Button'

type ExistingChangeRequestAlertType = {
  projectId: number | string
  environmentId: string
  featureId: number
  className?: string
  history: RouterChildContext['router']['history']
}

const ExistingChangeRequestAlert: FC<ExistingChangeRequestAlertType> = ({
  className,
  environmentId,
  featureId,
  history,
  projectId,
}) => {
  const date = useRef(moment().toISOString())

  const { data: changeRequests } = useGetChangeRequestsQuery(
    {
      committed: false,
      environmentId,
      feature_id: featureId,
    },
    { refetchOnMountOrArgChange: true },
  )

  const { data: scheduledChangeRequests } = useGetChangeRequestsQuery(
    {
      environmentId,
      feature_id: featureId,
      live_from_after: date.current,
    },
    { refetchOnMountOrArgChange: true },
  )

  const handleNavigate = () => {
    const changes = scheduledChangeRequests?.results?.length
      ? scheduledChangeRequests?.results
      : changeRequests?.results
    const latestChangeRequest = changes?.at(-1)?.id
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
    !!scheduledChangeRequests?.results?.length,
    !!changeRequests?.results?.length,
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
