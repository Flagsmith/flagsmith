import { FC } from 'react'
import { ChangeRequestSummary } from 'common/types/responses'
import { colorIconSecondary } from 'common/theme/tokens'
import Accordion from 'components/base/Accordion'
import Banner from 'components/base/Banner'
import Chip from 'components/base/Chip'
import Icon from 'components/icons/Icon'
import Skeleton from 'components/Skeleton'
import DependencyChangesTable from 'components/feature-dependencies/DependencyChangesTable'
import { useDependencyChanges } from 'components/feature-dependencies/useDependencyChanges'
import ChangeRequestLink from 'components/modals/create-feature/tabs/FeatureDependenciesTab/ChangeRequestLink'

type PendingChangeRequestProps = {
  changeRequest: ChangeRequestSummary
  environmentId: string
  featureId: number
  projectId: number
  isEnabled: (prerequisiteId: number) => boolean
}

// One open change request, shown only if it changes this feature's
// prerequisites. Each loads its own, as the change request page does.
const PendingChangeRequest: FC<PendingChangeRequestProps> = ({
  changeRequest,
  environmentId,
  featureId,
  isEnabled,
  projectId,
}) => {
  const { changes, isClosed, isError } = useDependencyChanges({
    changeRequestId: changeRequest.id,
    environmentId,
    featureId,
  })

  if (isClosed) return null
  if (isError) {
    return (
      <Banner type='error'>
        Could not load the dependency changes in #{changeRequest.id}{' '}
        {changeRequest.title}.
      </Banner>
    )
  }
  if (!changes) return <Skeleton width='100%' height={56} aria-hidden />
  // Most change sets only touch values or overrides.
  if (!changes.length) return null

  return (
    <Accordion
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
          <Chip className='ms-auto flex-shrink-0' size='xs' variant='warning'>
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
  )
}

export default PendingChangeRequest
