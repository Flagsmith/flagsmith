import { FC } from 'react'
import { useGetFeatureDependenciesQuery } from 'common/services/useFeatureDependency'
import { diffDependencies } from 'common/utils/diffDependencies'
import DependencyChangesTable from './DependencyChangesTable'
import ErrorMessage from 'components/ErrorMessage'

type ChangeRequestDependencyChangesProps = {
  environmentId: string
  featureId: number
  changeRequestId: number
  isEnabled?: (prerequisiteId: number) => boolean
}

// A feature's prerequisite changes in one change request: its dependencies
// as if the change request were live, against today's.
const ChangeRequestDependencyChanges: FC<
  ChangeRequestDependencyChangesProps
> = ({ changeRequestId, environmentId, featureId, isEnabled }) => {
  const live = useGetFeatureDependenciesQuery({ environmentId, featureId })
  const scoped = useGetFeatureDependenciesQuery({
    changeRequestId,
    environmentId,
    featureId,
  })

  if (live.isLoading || scoped.isLoading) {
    return (
      <div className='text-center p-3'>
        <Loader />
      </div>
    )
  }
  if (live.isError || scoped.isError || !live.data || !scoped.data) {
    return <ErrorMessage error='Could not load the prerequisite changes.' />
  }

  const changes = diffDependencies(live.data.results, scoped.data.results)
  if (!changes.length) {
    return (
      <p className='text-secondary px-3 py-2 mb-0'>No prerequisite changes.</p>
    )
  }
  return <DependencyChangesTable changes={changes} isEnabled={isEnabled} />
}

export default ChangeRequestDependencyChanges
