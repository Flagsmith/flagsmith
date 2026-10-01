import { FC, ReactNode } from 'react'
import EmptyState from 'components/EmptyState'
import { THROTTLED } from 'components/pages/usage/throttle'

export type UsagePageLayoutProps = {
  isError?: boolean
  isLoading?: boolean
  /** The error is the rate limit, so it says to wait rather than that it broke. */
  isThrottled?: boolean
  onRetry?: () => void
  /** Outlives the loading and error states: a restricted organisation needs
   * to know why it is cut off even when the usage request fails. */
  alert?: ReactNode
  children?: ReactNode
}

const UsagePageLayout: FC<UsagePageLayoutProps> = ({
  alert,
  children,
  isError,
  isLoading,
  isThrottled,
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
        title={isThrottled ? THROTTLED.title : 'Usage could not be loaded'}
        description={
          isThrottled
            ? THROTTLED.description
            : 'Something went wrong fetching usage for this period. Try again in a moment.'
        }
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
      {alert}
      {content}
    </div>
  )
}

export default UsagePageLayout
