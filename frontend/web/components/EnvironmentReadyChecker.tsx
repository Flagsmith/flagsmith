import { PropsWithChildren, useEffect, useRef, useState } from 'react'
import { useHistory } from 'react-router-dom'
import {
  useGetEnvironmentQuery,
  useGetEnvironmentsQuery,
} from 'common/services/useEnvironment'
import { useRouteContext } from './providers/RouteContext'
import { shouldRedirectMissingEnvironment } from 'common/utils/shouldRedirectMissingEnvironment'

type EnvironmentReadyCheckerType = {
  children: React.ReactNode
}

const EnvironmentReadyChecker = ({
  children,
}: PropsWithChildren<EnvironmentReadyCheckerType>) => {
  const history = useHistory()
  const { environmentId, projectId } = useRouteContext()
  const [environmentCreated, setEnvironmentCreated] = useState(false)
  const hasRedirected = useRef(false)

  // 'create' is the new-environment form route sentinel, not an env api_key.
  const hasEnvironmentId = !!environmentId && environmentId !== 'create'

  const {
    data,
    error: envByIdError,
    isLoading: isLoadingEnvById,
  } = useGetEnvironmentQuery(
    { id: environmentId || '' },
    {
      pollingInterval: 1000,
      skip: !hasEnvironmentId || environmentCreated,
    },
  )

  const { data: environmentsData, isLoading: isLoadingEnvironments } =
    useGetEnvironmentsQuery({ projectId: projectId ?? 0 }, { skip: !projectId })

  useEffect(() => {
    if (!!data && !data?.is_creating) {
      setEnvironmentCreated(true)
    }
  }, [data])

  // Redirect to the project's default environment when the URL points at an
  // environment that does not exist for this project. Fixes Flagsmith#7446.
  useEffect(() => {
    if (!projectId) return

    const shouldRedirect = shouldRedirectMissingEnvironment({
      envByIdError,
      environmentId,
      environmentsData,
      hasEnvironmentId,
      hasRedirected: hasRedirected.current,
      isLoadingEnvById,
      isLoadingEnvironments,
    })

    if (shouldRedirect) {
      hasRedirected.current = true
      history.replace(`/project/${projectId}/`)
    }
  }, [
    envByIdError,
    environmentId,
    environmentsData,
    hasEnvironmentId,
    history,
    isLoadingEnvById,
    isLoadingEnvironments,
    projectId,
  ])

  if (!hasEnvironmentId) {
    return children
  }
  if (isLoadingEnvById || isLoadingEnvironments) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }
  if (data?.is_creating) {
    return (
      <div className='container'>
        <div className='d-flex flex-column h-100 flex-1 justify-content-center align-items-center'>
          <Loader />
          <h3>Preparing your environment</h3>
          <p>We are setting up your new environment...</p>
        </div>
      </div>
    )
  }
  // Keep the loader on screen while a redirect is in-flight or the
  // env-by-id query has produced no data yet. Without this guard, children
  // would mount with an invalid environmentId — the root cause of the
  // infinite loader prior to this fix.
  if (hasRedirected.current || !data) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }
  return children
}

export default EnvironmentReadyChecker
