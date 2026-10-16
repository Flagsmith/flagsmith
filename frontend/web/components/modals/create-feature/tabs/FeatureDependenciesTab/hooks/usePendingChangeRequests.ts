import { skipToken } from '@reduxjs/toolkit/query'
import { useRef } from 'react'
import { useGetChangeRequestsQuery } from 'common/services/useChangeRequest'
import {
  useGetFeatureDependenciesQuery,
  useGetPendingFeatureDependenciesQuery,
} from 'common/services/useFeatureDependency'
import { diffDependencies } from 'common/utils/diffDependencies'

type UsePendingChangeRequestsArgs = {
  environmentId: string
  featureId: number
}

// The open change requests that change this feature's prerequisites, with
// what each one changes. Scheduled ones are left out, as the API refuses to
// list their dependencies.
export const usePendingChangeRequests = ({
  environmentId,
  featureId,
}: UsePendingChangeRequestsArgs) => {
  // Matches any change request with a change set for this feature.
  const open = useGetChangeRequestsQuery({
    committed: false,
    environmentId,
    feature_id: featureId,
    page_size: 100,
  })
  const changeRequestIds = open.data?.results.map(({ id }) => id)
  const live = useGetFeatureDependenciesQuery({ environmentId, featureId })
  const pending = useGetPendingFeatureDependenciesQuery(
    changeRequestIds?.length
      ? { changeRequestIds, environmentId, featureId }
      : skipToken,
  )

  // Most change sets only touch values or overrides, so those drop out.
  const changeRequests = (open.data?.results ?? []).flatMap((changeRequest) => {
    const scoped = pending.data?.find(
      ({ changeRequestId }) => changeRequestId === changeRequest.id,
    )
    if (!scoped || !live.data) return []
    const changes = diffDependencies(live.data.results, scoped.results)
    return changes.length ? [{ changeRequest, changes }] : []
  })

  // These queries refetch independently on focus. Keep the last complete
  // result visible rather than briefly rendering a mixture of old and new
  // snapshots as each request settles.
  const lastSettledChangeRequests = useRef(changeRequests)
  const isFetching = open.isFetching || live.isFetching || pending.isFetching
  if (!isFetching) lastSettledChangeRequests.current = changeRequests

  return {
    changeRequests: isFetching
      ? lastSettledChangeRequests.current
      : changeRequests,
    // A failed list would otherwise read as nothing pending.
    isError: open.isError || live.isError || pending.isError,
  }
}
