import { FC } from 'react'
import DependencyChangesTable from './DependencyChangesTable'
import { useDependencyChanges } from './useDependencyChanges'
import ErrorMessage from 'components/ErrorMessage'

type ChangeRequestDependencyChangesProps = {
  environmentId: string
  featureId: number
  changeRequestId: number
  isEnabled?: (prerequisiteId: number) => boolean
}

const ChangeRequestDependencyChanges: FC<
  ChangeRequestDependencyChangesProps
> = ({ changeRequestId, environmentId, featureId, isEnabled }) => {
  const { changes, isError, isLoading } = useDependencyChanges({
    changeRequestId,
    environmentId,
    featureId,
  })

  if (isLoading) {
    return (
      <div className='text-center p-3'>
        <Loader />
      </div>
    )
  }
  if (isError || !changes) {
    return <ErrorMessage error='Could not load the prerequisite changes.' />
  }
  if (!changes.length) {
    return (
      <p className='text-secondary px-3 py-2 mb-0'>No prerequisite changes.</p>
    )
  }
  return <DependencyChangesTable changes={changes} isEnabled={isEnabled} />
}

export default ChangeRequestDependencyChanges
