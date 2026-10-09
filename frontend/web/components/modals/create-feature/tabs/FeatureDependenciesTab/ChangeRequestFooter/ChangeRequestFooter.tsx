import { FC } from 'react'
import Button from 'components/base/forms/Button'
import { SubmitProgress } from 'components/modals/create-feature/tabs/FeatureDependenciesTab/hooks/useStagedPrerequisites'
import './ChangeRequestFooter.scss'

type ChangeRequestFooterProps = {
  count: number
  progress: SubmitProgress | null
  onCreate: () => void
  onDiscard: () => void
}

// The calls run one after another, so say which one is in flight.
const describeProgress = (progress: SubmitProgress) =>
  progress.done === null
    ? 'Creating change request…'
    : `Staging ${progress.done + 1} of ${progress.total}…`

const ChangeRequestFooter: FC<ChangeRequestFooterProps> = ({
  count,
  onCreate,
  onDiscard,
  progress,
}) => (
  <div className='change-request-footer d-flex align-items-center gap-2'>
    <span className='text-secondary me-auto' aria-live='polite'>
      {/* Keyed on the count, so each change replays the pulse. */}
      <span key={count} className='change-request-footer__count'>
        {count}
      </span>{' '}
      {count === 1 ? 'change' : 'changes'} staged
    </span>
    <Button theme='secondary' onClick={onDiscard} disabled={!!progress}>
      Discard changes
    </Button>
    <Button onClick={onCreate} isLoading={!!progress}>
      {progress ? describeProgress(progress) : 'Create Change Request'}
    </Button>
  </div>
)

export default ChangeRequestFooter
