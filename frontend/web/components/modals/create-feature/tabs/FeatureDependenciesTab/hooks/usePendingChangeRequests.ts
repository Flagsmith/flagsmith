import { useRef } from 'react'
import { useGetChangeRequestsQuery } from 'common/services/useChangeRequest'
import { useGetChangeRequestIdsStagingQuery } from 'common/services/useFeatureDependency'

type UsePendingChangeRequestsArgs = {
  environmentId: string
  featureId: number
}

// The open and scheduled change requests staging changes to this feature's
// dependencies.
export const usePendingChangeRequests = ({
  environmentId,
  featureId,
}: UsePendingChangeRequestsArgs) => {
  const now = useRef(new Date().toISOString())
  const staging = useGetChangeRequestIdsStagingQuery({ featureId })
  // One page is enough until the API lists change requests by feature.
  const open = useGetChangeRequestsQuery({
    committed: false,
    environmentId,
    page_size: 100,
  })
  const scheduled = useGetChangeRequestsQuery({
    committed: true,
    environmentId,
    live_from_after: now.current,
    page_size: 100,
  })

  // One that was published or deleted is in neither list, so it drops out.
  const changeRequests = [
    ...(open.data?.results ?? []),
    ...(scheduled.data?.results ?? []),
  ].filter((changeRequest) => staging.data?.includes(changeRequest.id))

  return {
    changeRequests,
    // A failed list would otherwise read as nothing pending.
    isError:
      staging.isError ||
      (!!staging.data?.length && (open.isError || scheduled.isError)),
  }
}
