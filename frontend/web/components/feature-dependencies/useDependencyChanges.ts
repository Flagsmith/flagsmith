import { skipToken } from '@reduxjs/toolkit/query'
import { useGetFeatureDependenciesQuery } from 'common/services/useFeatureDependency'
import { diffDependencies } from 'common/utils/diffDependencies'

type UseDependencyChangesArgs = {
  environmentId: string
  featureId: number
  changeRequestId: number
  skip?: boolean
}

// A feature's prerequisite changes in one change request: its dependencies
// as if the change request were live, against today's.
export const useDependencyChanges = ({
  changeRequestId,
  environmentId,
  featureId,
  skip,
}: UseDependencyChangesArgs) => {
  const live = useGetFeatureDependenciesQuery(
    skip ? skipToken : { environmentId, featureId },
  )
  const scoped = useGetFeatureDependenciesQuery(
    skip ? skipToken : { changeRequestId, environmentId, featureId },
  )
  const isError = live.isError || scoped.isError
  const changes =
    live.data && scoped.data
      ? diffDependencies(live.data.results, scoped.data.results)
      : undefined
  return { changes, isError }
}
