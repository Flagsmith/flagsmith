import { FC } from 'react'
import ErrorMessage from './ErrorMessage'

type EnvironmentsLoadStateProps = {
  isError: boolean
  isLoading: boolean
}

const EnvironmentsLoadState: FC<EnvironmentsLoadStateProps> = ({
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
    return (
      <ErrorMessage error='Could not load environments for this project.' />
    )
  }
  return null
}

export default EnvironmentsLoadState
