import { FC } from 'react'
import Accordion from 'components/base/Accordion'
import ChangeRequestLink from 'components/modals/create-feature/tabs/FeatureDependenciesTab/ChangeRequestLink'
import Chip from 'components/base/Chip'
import Icon from 'components/icons/Icon'
import { colorIconSecondary } from 'common/theme/tokens'
import Banner from 'components/base/Banner'
import DependencyChangesTable from 'components/feature-dependencies/DependencyChangesTable'
import { usePendingChangeRequests } from 'components/modals/create-feature/tabs/FeatureDependenciesTab/hooks/usePendingChangeRequests'

type PendingChangeRequestsProps = {
  environmentId: string
  featureId: number
  projectId: number
  isEnabled: (prerequisiteId: number) => boolean
}

// Changes to this feature's prerequisites that are waiting in open change
// requests, one group per change request.
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
      <Banner type='error' className='mt-4'>
        Could not load the change requests waiting on this feature.
      </Banner>
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
        {groups.map(({ changeRequest, changes }) => (
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
                <Chip
                  className='ms-auto flex-shrink-0'
                  size='xs'
                  variant='warning'
                >
                  Awaiting approval
                </Chip>
              </>
            }
          >
            <DependencyChangesTable changes={changes} isEnabled={isEnabled} />
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

export default PendingChangeRequests
