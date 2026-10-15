import { FC } from 'react'
import { ChangeRequestSummary } from 'common/types/responses'
import Accordion from 'components/base/Accordion'
import ChangeRequestLink from 'components/modals/create-feature/tabs/FeatureDependenciesTab/ChangeRequestLink'
import Chip from 'components/base/Chip'
import Icon from 'components/icons/Icon'
import { colorIconSecondary } from 'common/theme/tokens'
import ErrorMessage from 'components/ErrorMessage'
import ChangeRequestDependencyChanges from 'components/feature-dependencies/ChangeRequestDependencyChanges'
import {
  describeStatus,
  isScheduled,
} from 'components/modals/create-feature/tabs/FeatureDependenciesTab/pendingChangeRequestState'
import { usePendingChangeRequests } from 'components/modals/create-feature/tabs/FeatureDependenciesTab/hooks/usePendingChangeRequests'

type PendingChangeRequestsProps = {
  environmentId: string
  featureId: number
  projectId: number
  isEnabled: (prerequisiteId: number) => boolean
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
          <Accordion
            key={changeRequest.id}
            defaultOpen
            flush
            title={
              <>
                <Icon
                  name='request'
                  width={16}
                  fill={colorIconSecondary}
                  aria-hidden
                />
                #{changeRequest.id} {changeRequest.title}
                <StatusChip
                  className='ms-auto flex-shrink-0'
                  changeRequest={changeRequest}
                />
              </>
            }
          >
            <ChangeRequestDependencyChanges
              environmentId={environmentId}
              featureId={featureId}
              changeRequestId={changeRequest.id}
              isEnabled={isEnabled}
            />
            {/* In the body, as the header is the toggle and a link cannot
                sit inside a button. */}
            <div className='px-3 py-2'>
              <ChangeRequestLink
                projectId={projectId}
                environmentId={environmentId}
                changeRequestId={changeRequest.id}
              >
                View change request
              </ChangeRequestLink>
            </div>
          </Accordion>
        ))}
      </div>
    </div>
  )
}

// Waiting on people reads as a warning; a scheduled change only needs time.
const StatusChip: FC<{
  changeRequest: ChangeRequestSummary
  className?: string
}> = ({ changeRequest, className }) => (
  <Chip
    className={className}
    size='xs'
    variant={isScheduled(changeRequest) ? undefined : 'warning'}
  >
    {describeStatus(changeRequest)}
  </Chip>
)

export default PendingChangeRequests
