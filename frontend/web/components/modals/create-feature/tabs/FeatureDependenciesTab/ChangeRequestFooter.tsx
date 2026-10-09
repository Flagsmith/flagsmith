import { FC } from 'react'
import Button from 'components/base/forms/Button'

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
  <div className='d-flex align-items-center gap-2 mt-3'>
    <span className='text-secondary me-auto'>
      {count} {count === 1 ? 'change' : 'changes'} staged
    </span>
    <Button theme='secondary' onClick={onDiscard} disabled={isSubmitting}>
      Discard changes
    </Button>
    <Button onClick={onCreate} isLoading={isSubmitting} disabled={isSubmitting}>
      Create Change Request
    </Button>
  </div>
)

export default ChangeRequestFooter
