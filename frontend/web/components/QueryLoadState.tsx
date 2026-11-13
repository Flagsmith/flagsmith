import { FC } from 'react'
import ErrorMessage from './ErrorMessage'

type QueryLoadStateProps = {
  errorMessage: string
  isError: boolean
  isLoading: boolean
}

const QueryLoadState: FC<QueryLoadStateProps> = ({
  errorMessage,
  isError,
  isLoading,
}) => {
  if (isLoading) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }
  if (isError) {
    return <ErrorMessage error={errorMessage} />
  }
  return null
}

export default QueryLoadState
