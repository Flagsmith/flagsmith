import { PropsWithChildren, useEffect, useState } from 'react'
import { useGetEnvironmentQuery } from 'common/services/useEnvironment'
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
  // 'create' is the new-env form route sentinel, not an env ID.
  const hasEnvironmentId = !!environmentId && environmentId !== 'create'

  // Gate pollingInterval on a state flag rather than reading `data` inside the
  // hook options: `data` is the same hook's destructured result and is
  // unassigned at options-evaluation time, so a direct reference silently
  // evaluates to `undefined` and polling never starts.
  const [pollingStopped, setPollingStopped] = useState(false)

  useEffect(() => {
    setPollingStopped(false)
  }, [environmentId])

  const { data, isError } = useGetEnvironmentQuery(
    { id: environmentId || '' },
    {
      pollingInterval: pollingStopped ? 0 : POLL_INTERVAL_MS,
      skip: !hasEnvironmentId,
    },
  )

  // Env-by-api_key endpoint isn't project-scoped — verify the match client-side.
  const wrongProject =
    !!data && !!projectId && data.project !== Number(projectId)
  const environmentNotFound = hasEnvironmentId && (wrongProject || isError)

  useEffect(() => {
    if ((data && !data.is_creating) || isError || wrongProject) {
      setPollingStopped(true)
    }
  }, [data, isError, wrongProject])

  if (!hasEnvironmentId) return children
  if (environmentNotFound) return <NotFoundState />
  if (!data) return <LoadingState />
  if (data.is_creating) return <CreatingState />
  return children
}

export default EnvironmentReadyChecker
