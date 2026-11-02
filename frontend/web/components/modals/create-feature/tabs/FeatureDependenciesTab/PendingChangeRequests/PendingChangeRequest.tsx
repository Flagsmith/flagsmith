import { FC } from 'react'
import { ChangeRequestSummary } from 'common/types/responses'
import { colorIconSecondary } from 'common/theme/tokens'
import Accordion from 'components/base/Accordion'
import Banner from 'components/base/Banner'
import Icon from 'components/icons/Icon'
import Skeleton from 'components/Skeleton'
import DependencyChangesTable from 'components/feature-dependencies/DependencyChangesTable'
import { useDependencyChanges } from 'components/feature-dependencies/useDependencyChanges'
import { countDependencyChanges } from 'common/utils/diffDependencies'
import ChangeRequestLink from 'components/modals/create-feature/tabs/FeatureDependenciesTab/ChangeRequestLink'

type PendingChangeRequestProps = {
  changeRequest: ChangeRequestSummary
  environmentId: string
  featureId: number
  projectId: number
  isEnabled: (prerequisiteId: number) => boolean
  defaultOpen: boolean
}

// One open change request, shown only if it changes this feature's
// prerequisites. Each loads its own, as the change request page does.
const PendingChangeRequest: FC<PendingChangeRequestProps> = ({
  changeRequest,
  defaultOpen,
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

  const { added, label, removed } = countDependencyChanges(changes)

  return (
    <Accordion
      defaultOpen={defaultOpen}
      flush
      title={
        <>
          <Icon
            name='request'
            width={16}
            fill={colorIconSecondary}
            aria-hidden
          />
          <span className='pending-change-requests__title text-truncate'>
            #{changeRequest.id} {changeRequest.title}
          </span>
          {/* Read out as words, as "+1 −2" means little to a screen reader. */}
          <span
            className='pending-change-requests__count d-flex flex-shrink-0 justify-content-end gap-2 ms-auto'
            role='img'
            aria-label={label}
          >
            {!!added && <span className='text-success'>+{added}</span>}
            {!!removed && <span className='text-danger'>−{removed}</span>}
          </span>
        </>
      }
    >
      <DependencyChangesTable changes={changes} isEnabled={isEnabled} />
      {/* In the body, as the header is the toggle and a link cannot
          sit inside a button. */}
      <div className='d-flex justify-content-end px-3 py-2'>
        <ChangeRequestLink
          className='pending-change-requests__link text-action'
          projectId={projectId}
          environmentId={environmentId}
          changeRequestId={changeRequest.id}
        >
          Open #{changeRequest.id}
        </ChangeRequestLink>
      </div>
    </Accordion>
  )
}

export default PendingChangeRequest
