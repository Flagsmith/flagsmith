import { FC, ReactNode } from 'react'
import EmptyState from 'components/EmptyState'

export type UsagePageLayoutProps = {
  isError?: boolean
  isLoading?: boolean
  onRetry?: () => void
  children?: ReactNode
}

const UsagePageLayout: FC<UsagePageLayoutProps> = ({
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

export default UsagePageLayout
