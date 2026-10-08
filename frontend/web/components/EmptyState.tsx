import { FC } from 'react'
import Link from './base/link'
import StateMessage, { StateMessageProps } from './StateMessage'

type EmptyStateProps = Omit<StateMessageProps, 'role'> & {
  docsUrl?: string
  docsLabel?: string
}

const EmptyState: FC<EmptyStateProps> = ({
  action,
  docsLabel = 'View docs',
  docsUrl,
  ...props
}) => (
  <StateMessage
    {...props}
    action={
      <>
        {docsUrl && (
          <Link href={docsUrl} target='_blank'>
            {docsLabel}
          </Link>
        )}
        {action}
      </>
    }
  />
)

export default EmptyState
