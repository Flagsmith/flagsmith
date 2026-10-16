import { skipToken } from '@reduxjs/toolkit/query'
import { useGetFeatureDependenciesQuery } from 'common/services/useFeatureDependency'
import { diffDependencies } from 'common/utils/diffDependencies'

type UseDependencyChangesArgs = {
  environmentId: string
  featureId: number
  changeRequestId: number
  skip?: boolean
}

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
  const status =
    scoped.error && 'status' in scoped.error ? scoped.error.status : undefined
  // Published or deleted since it was listed.
  const isClosed = status === 400 || status === 404
  const isError = live.isError || (scoped.isError && !isClosed)
  const changes =
    live.data && scoped.data
      ? diffDependencies(live.data.results, scoped.data.results)
      : undefined
  return { changes, isClosed, isError }
}
