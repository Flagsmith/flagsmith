import NotFoundPage from 'components/pages/NotFoundPage'
import React from 'react'
import { RouteComponentProps, Route } from 'react-router-dom'
import EnvironmentReadyChecker from 'components/EnvironmentReadyChecker'
import { RouteProvider } from 'components/providers/RouteContext'
import { useProjectEnvironments } from 'common/hooks/useProjectEnvironments'
type ParameterizedRouteType = {
  component: React.ComponentType<any>
  [key: string]: any
}

export const ParameterizedRoute = ({
  component: Component,
  ...props
}: ParameterizedRouteType) => {
  const { organisationId, projectId } = props.computedMatch?.params || {}

  const parsedOrganisationId = organisationId && parseInt(organisationId)
  const parsedProjectId = projectId && parseInt(projectId)

  // Handle the case where the parameters are invalid
  if (
    (projectId && isNaN(parseInt(projectId))) ||
    (organisationId && isNaN(parseInt(organisationId)))
  ) {
    return <Route {...props} component={NotFoundPage} />
  }

  if (!projectId && !organisationId) {
    return <Route {...props} component={Component} />
  }

  const RouteContent = (componentProps: RouteComponentProps) => {
    // Get environmentKey from route param (still named :environmentId in routes)
    const environmentKey = componentProps.match.params.environmentId

    // Convert environmentKey to numeric environmentId if we have a projectId
    const { getEnvironmentIdFromKey } = useProjectEnvironments(
      parsedProjectId || 0,
    )
    const environmentId = environmentKey
      ? getEnvironmentIdFromKey(environmentKey)
      : undefined

    return (
      <RouteProvider
        value={{
          environmentId,
          environmentKey,
          organisationId: parsedOrganisationId,
          projectId: parsedProjectId,
        }}
      >
        <EnvironmentReadyChecker
          match={{
            ...componentProps.match,
            params: {
              environmentId: componentProps.match.params.environmentId,
            },
          }}
        >
          <Component
            {...componentProps}
            match={{
              ...componentProps.match,
              params: {
                ...componentProps.match.params,
                ...(organisationId && {
                  organisationId: parsedOrganisationId,
                }),
                ...(projectId && { projectId: parsedProjectId }),
              },
            }}
          />
        </EnvironmentReadyChecker>
      </RouteProvider>
    )
  }

  return <Route {...props} render={RouteContent} />
}
