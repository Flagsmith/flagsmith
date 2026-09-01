import { FC, ReactNode } from 'react'
import EmptyState from 'components/EmptyState'

export type UsageDashboardProps = {
  isError?: boolean
  isLoading?: boolean
  onRetry?: () => void
  children?: ReactNode
}

/**
 * The page frame: heading, and the two states where there is nothing to lay
 * out. What the dashboard is made of is composed by the caller.
 */
const UsageDashboard: FC<UsageDashboardProps> = ({
  children,
  isError,
  isLoading,
  onRetry,
}) => {
  let content = children

  if (isLoading) {
    content = (
      <div className='text-center'>
        <Loader />
      </div>
    )
  } else if (isError) {
    content = (
      <EmptyState
        title='Usage could not be loaded'
        description='Something went wrong fetching usage for this period. Try again in a moment.'
        icon='bar-chart'
        action={
          onRetry && (
            <Button onClick={onRetry} theme='secondary'>
              Try again
            </Button>
          )
        }
      />
    )
  }

  return (
    <div className='px-3 px-md-4 py-4'>
      <h4 className='mb-4'>Usage</h4>
      {content}
    </div>
  )
}

export default UsageDashboard
