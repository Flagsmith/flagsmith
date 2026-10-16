import { FC } from 'react'
import { useGetChangeRequestsQuery } from 'common/services/useChangeRequest'
import Banner from 'components/base/Banner'
import PendingChangeRequest from './PendingChangeRequest'
import './PendingChangeRequests.scss'

type PendingChangeRequestsProps = {
  environmentId: string
  featureId: number
  projectId: number
  isEnabled: (prerequisiteId: number) => boolean
}

// Changes to this feature's prerequisites that are waiting in open change
// requests, one group per change request. Scheduled ones are left out, as
// the API refuses to list their dependencies.
const PendingChangeRequests: FC<PendingChangeRequestsProps> = ({
  environmentId,
  featureId,
  isEnabled,
  projectId,
}) => {
  // Matches any change request with a change set for this feature.
  const { data, isError } = useGetChangeRequestsQuery({
    committed: false,
    environmentId,
    feature_id: featureId,
    page_size: 100,
  })

  if (isError) {
    return (
      <Banner type='error' className='mt-4'>
        Could not load the change requests waiting on this feature.
      </Banner>
    )
  }

  if (!data?.results.length) return null

  return (
    <div className='pending-change-requests mt-4'>
      <h6 className='mb-1'>Pending in change requests</h6>
      <p className='text-secondary mb-3'>
        Not live yet. These go live when their change request is published.
      </p>
      <div className='pending-change-requests__list d-flex flex-column gap-3'>
        {data.results.map((changeRequest) => (
          <PendingChangeRequest
            key={changeRequest.id}
            changeRequest={changeRequest}
            environmentId={environmentId}
            featureId={featureId}
            projectId={projectId}
            isEnabled={isEnabled}
          />
        ))}
      </div>
    </div>
  )
}

export default PendingChangeRequests
