import { FC, useEffect, useMemo, useRef } from 'react'
import cn from 'classnames'
import moment from 'moment'
import { ChangeRequestSummary } from 'common/types/responses'
import { useGetChangeRequestsQuery } from 'common/services/useChangeRequest'
import { useGetPendingDependencyChangesQuery } from 'common/services/useFeatureDependency'
import Accordion from 'components/base/Accordion'
import ChangeRequestLink from 'components/modals/create-feature/tabs/FeatureDependenciesTab/ChangeRequestLink'
import Chip from 'components/base/Chip'
import ErrorMessage from 'components/ErrorMessage'
import DependencyChangesTable from 'components/DependencyChangesTable'
import './PendingChangeRequests.scss'

type PendingChangeRequestsProps = {
  environmentId: string
  featureId: number
  projectId: number
  // The change request just created, flashed and scrolled to on arrival.
  highlightId?: number
}

// Changes to this feature's prerequisites that are waiting in open or
// scheduled change requests, one group per change request.
const PendingChangeRequests: FC<PendingChangeRequestsProps> = ({
  environmentId,
  featureId,
  highlightId,
  projectId,
}) => {
  const now = useRef(new Date().toISOString())
  const highlightRef = useRef<HTMLDivElement>(null)
  const { data: pending } = useGetPendingDependencyChangesQuery({ featureId })
  const { data: open, isError: isOpenError } = useGetChangeRequestsQuery({
    committed: false,
    environmentId,
    page_size: 100,
  })
  const { data: scheduled, isError: isScheduledError } =
    useGetChangeRequestsQuery({
      committed: true,
      environmentId,
      live_from_after: now.current,
      page_size: 100,
    })

  // A change request that was published or deleted has nothing pending.
  const groups = useMemo(() => {
    const live = [...(open?.results ?? []), ...(scheduled?.results ?? [])]
    return (pending ?? []).flatMap(({ changeRequestId, changes }) => {
      const changeRequest = live.find((cr) => cr.id === changeRequestId)
      return changeRequest ? [{ changeRequest, changes }] : []
    })
  }, [pending, open, scheduled])

  const hasHighlight = groups.some(
    ({ changeRequest }) => changeRequest.id === highlightId,
  )
  useEffect(() => {
    if (!hasHighlight) return
    const reduceMotion = window.matchMedia(
      '(prefers-reduced-motion: reduce)',
    ).matches
    highlightRef.current?.scrollIntoView({
      behavior: reduceMotion ? 'auto' : 'smooth',
      block: 'nearest',
    })
  }, [hasHighlight])

  // Without the change request lists, staged changes cannot be matched to
  // one, and hiding them would read as nothing pending.
  if (pending?.length && (isOpenError || isScheduledError)) {
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
        {groups.map(({ changeRequest, changes }) => (
          <div
            key={changeRequest.id}
            ref={changeRequest.id === highlightId ? highlightRef : undefined}
            className={cn({
              'pending-change-request--flash': changeRequest.id === highlightId,
            })}
          >
            <Accordion
              defaultOpen
              flush
              title={`#${changeRequest.id} ${changeRequest.title}`}
              meta={<Chip size='xs'>{describeStatus(changeRequest)}</Chip>}
            >
              <DependencyChangesTable changes={changes} />
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
          </div>
        ))}
      </div>
    </div>
  )
}

const describeStatus = (changeRequest: ChangeRequestSummary) =>
  changeRequest.committed_at && changeRequest.live_from
    ? `Scheduled for ${moment(changeRequest.live_from).format('D MMM, HH:mm')}`
    : 'Awaiting approval'

export default PendingChangeRequests
