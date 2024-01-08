import { FC } from 'react'
import { useGetChangeRequestsQuery } from 'common/services/useChangeRequest'
import WarningMessage from './WarningMessage'
import moment from 'moment'

type ExistingChangeRequestAlertType = {
  environmentId: string
  featureId: number
  className?: string
}

const ExistingChangeRequestAlert: FC<ExistingChangeRequestAlertType> = ({
  className,
  environmentId,
  featureId,
}) => {
  const { data } = useGetChangeRequestsQuery({
    committed: false,
    environmentId,
    feature_id: featureId,
  })
  const { data: scheduledChangeRequests } = useGetChangeRequestsQuery({
    environmentId,
    feature_id: featureId,
    live_from_after: moment().startOf('hour').toISOString(),
  })

  if (scheduledChangeRequests?.results?.length) {
    return (
      <div className={className}>
        <WarningMessage
          warningMessage={
            'You have scheduled changes upcoming for this feature, please check the Scheduling page.'
          }
        />
      </div>
    )
  }
  if (data?.results?.length) {
    return (
      <div className={className}>
        <WarningMessage
          warningMessage={
            'You have open change requests for this feature, please check the Change Requests page.'
          }
        />
      </div>
    )
  }
  return null
}

export default ExistingChangeRequestAlert
