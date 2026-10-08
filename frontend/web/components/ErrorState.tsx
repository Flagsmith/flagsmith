import { FC } from 'react'
import Button from './base/forms/Button'
import StateMessage, { StateMessageProps } from './StateMessage'

type ErrorStateProps = Omit<StateMessageProps, 'action' | 'role'> & {
  onRetry?: () => void
}

const ErrorState: FC<ErrorStateProps> = ({
  icon = 'warning',
  onRetry,
  ...props
}) => (
  <StateMessage
    {...props}
    icon={icon}
    role='alert'
    action={
      onRetry && (
        <Button theme='secondary' onClick={onRetry}>
          Try again
        </Button>
      )
    }
  />
)

export default ErrorState
