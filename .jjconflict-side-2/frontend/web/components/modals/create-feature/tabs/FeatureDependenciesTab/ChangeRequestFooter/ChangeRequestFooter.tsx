import { FC } from 'react'
import Button from 'components/base/forms/Button'
import './ChangeRequestFooter.scss'

type ChangeRequestFooterProps = {
  count: number
  isSubmitting: boolean
  onCreate: () => void
  onDiscard: () => void
}

const ChangeRequestFooter: FC<ChangeRequestFooterProps> = ({
  count,
  isSubmitting,
  onCreate,
  onDiscard,
}) => (
  <div className='change-request-footer position-sticky bottom-0 d-flex align-items-center gap-2 mt-3 p-3 bg-surface-default'>
    <span className='text-secondary me-auto' aria-live='polite'>
      {count} {count === 1 ? 'change' : 'changes'} staged
    </span>
    <Button theme='secondary' onClick={onDiscard} disabled={isSubmitting}>
      Discard changes
    </Button>
    <Button onClick={onCreate} isLoading={isSubmitting}>
      Create Change Request
    </Button>
  </div>
)

export default ChangeRequestFooter
