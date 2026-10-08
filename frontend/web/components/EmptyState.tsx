import { FC } from 'react'
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
          <a
            href={docsUrl}
            target='_blank'
            rel='noreferrer'
            className='btn btn-link'
          >
            {docsLabel}
          </a>
        )}
        {action}
      </>
    }
  />
)

export default EmptyState
