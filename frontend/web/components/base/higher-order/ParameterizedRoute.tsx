import NotFoundPage from 'components/pages/NotFoundPage'
import React from 'react'
import { RouteComponentProps, Route } from 'react-router-dom'

type ParameterizedRouteType = {
  component: React.ComponentType<any>
  [key: string]: any
}

export const ParameterizedRoute = ({
  component: Component,
  ...props
}: ParameterizedRouteType) => {
  const { organisationId, projectId } = props.computedMatch.params

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

  return (
    <Route
      {...props}
      render={(componentProps: RouteComponentProps) => (
        <Component
          {...componentProps}
          match={{
            ...componentProps.match,
            params: {
              ...componentProps.match.params,
              ...(organisationId && { organisationId: parsedOrganisationId }),
              ...(projectId && { projectId: parsedProjectId }),
            },
          }}
        />
      )}
    />
  )
}
