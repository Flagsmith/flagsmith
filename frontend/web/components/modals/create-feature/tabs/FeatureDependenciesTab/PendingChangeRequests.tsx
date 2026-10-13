import { FC } from 'react'
import Chip from 'components/base/Chip'
import ErrorMessage from 'components/ErrorMessage'
import ChangeRequestDependencyChanges from 'components/feature-dependencies/ChangeRequestDependencyChanges'
import DependenciesPanel from './DependenciesPanel'
import { describeStatus } from './pendingChangeRequestState'
import { usePendingChangeRequests } from './hooks/usePendingChangeRequests'

type PendingChangeRequestsProps = {
  environmentId: string
  featureId: number
  // Each prerequisite's state in this environment.
  isEnabled: (prerequisiteId: number) => boolean
  projectId: number
}

// Changes to this feature's prerequisites that are waiting in open or
// scheduled change requests, one group per change request.
const PendingChangeRequests: FC<PendingChangeRequestsProps> = ({
  environmentId,
  featureId,
  isEnabled,
  projectId,
}) => {
  const { changeRequests: groups, isError } = usePendingChangeRequests({
    environmentId,
    featureId,
  })

  if (isError) {
    return (
      <ErrorMessage error='Could not load the change requests waiting on this feature.' />
    )
  }

  if (!groups.length) return null

  return (
    <div className='mt-4'>
      <h6 className='mb-1'>Pending in change requests</h6>
      <p className='text-secondary mb-3'>
        Not live yet. These go live when their change request is published.
      </p>
      <div className='d-flex flex-column gap-3'>
        {groups.map((changeRequest) => (
          <DependenciesPanel key={changeRequest.id}>
            <div className='d-flex align-items-center gap-2 px-3 py-2'>
              <a
                className='fw-semibold me-auto text-truncate'
                href={`/project/${projectId}/environment/${environmentId}/change-requests/${changeRequest.id}`}
              >
                #{changeRequest.id} {changeRequest.title}
              </a>
              <Chip size='xs'>{describeStatus(changeRequest)}</Chip>
            </div>
            <ChangeRequestDependencyChanges
              environmentId={environmentId}
              featureId={featureId}
              changeRequestId={changeRequest.id}
              isEnabled={isEnabled}
            />
          </DependenciesPanel>
        ))}
      </div>
    </div>
  )
}

export default PendingChangeRequests
