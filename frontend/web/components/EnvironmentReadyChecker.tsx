import { PropsWithChildren, useEffect, useState } from 'react'
import {
  useGetEnvironmentQuery,
  useGetEnvironmentsQuery,
} from 'common/services/useEnvironment'
import { useRouteMatch } from 'react-router-dom'

interface RouteParams {
  projectId?: string
  environmentId?: string
}

type EnvironmentReadyCheckerType = {
  children: React.ReactNode
}

const POLL_INTERVAL_MS = 1000

const LoadingState = () => (
  <div className='text-center'>
    <Loader />
  </div>
)

const CreatingState = () => (
  <div className='container'>
    <div className='d-flex flex-column h-100 flex-1 justify-content-center align-items-center'>
      <Loader />
      <h3>Preparing your environment</h3>
      <p>We are setting up your new environment...</p>
    </div>
  </div>
)

const NotFoundState = () => (
  <div className='app-container container'>
    <h3 className='pt-5'>Environment not found</h3>
    <p>
      This environment may have been deleted, or you may not have permission to
      access it. Check the URL and try again.
    </p>
  </div>
)

const EnvironmentReadyChecker = ({
  children,
}: PropsWithChildren<EnvironmentReadyCheckerType>) => {
  const match = useRouteMatch<RouteParams>()
  const environmentId = match?.params?.environmentId
  const projectId = match?.params?.projectId
  // `/environment/create` is the new-env form — the slot is a sentinel, not an ID.
  const hasEnvironmentId = !!environmentId && environmentId !== 'create'
  const [pollingDone, setPollingDone] = useState(false)
  const [trackedEnvId, setTrackedEnvId] = useState(environmentId)

  // Reset during render when the URL env changes — keeps `skip` in sync with the
  // new env on the very first render, avoiding a flash of stale children.
  if (trackedEnvId !== environmentId) {
    setTrackedEnvId(environmentId)
    setPollingDone(false)
  }

  // Source of truth for "does this env belong to this project" — the backend
  // returns a single env by api_key regardless of project scope, so we can't
  // rely on a 4xx from the env endpoint alone.
  const { data: environments, isSuccess: environmentsLoaded } =
    useGetEnvironmentsQuery(
      { projectId: Number(projectId) },
      { skip: !projectId },
    )
  const envBelongsToProject = !!environments?.results?.some(
    (env) => env.api_key === environmentId,
  )
  const environmentNotFound =
    hasEnvironmentId && environmentsLoaded && !envBelongsToProject

  const { data, isLoading } = useGetEnvironmentQuery(
    { id: environmentId || '' },
    {
      pollingInterval: POLL_INTERVAL_MS,
      skip: !hasEnvironmentId || pollingDone || environmentNotFound,
    },
  )

  // Stop polling once the env resolves (not creating).
  useEffect(() => {
    if (data && !data.is_creating) {
      setPollingDone(true)
    }
  }, [data])

  if (!hasEnvironmentId) return children
  if (environmentNotFound) return <NotFoundState />
  if (isLoading || !environmentsLoaded) return <LoadingState />
  if (data?.is_creating) return <CreatingState />
  return children
}

export default EnvironmentReadyChecker
