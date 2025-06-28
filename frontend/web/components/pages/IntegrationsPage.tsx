import React, { FC, useEffect } from 'react'
import IntegrationList from 'components/IntegrationList'
import { useHasPermission } from 'common/providers/Permission'
import Constants from 'common/constants'
import PageTitle from 'components/PageTitle'
import InfoMessage from 'components/InfoMessage'
import { Link, useRouteMatch } from 'react-router-dom'
import Utils from 'common/utils/utils'
import AccountStore from 'common/stores/account-store'
import API from 'project/api'
import { useGetProjectQuery } from 'common/services/useProject'

interface RouteParams {
  projectId: string
}

export const integrationCategories = [
  'Analytics',
  'Authentication',
  'CI/CD',
  'Developer tools',
  'Infrastructure',
  'Messaging',
  'Monitoring',
  'Webhooks',
] as const
export type IntegrationSummary = {
  categories: (typeof integrationCategories)[number][]
  image: string
  title: string
}

export type IntegrationCategoryDescription = {
  category: (typeof integrationCategories)[number]
  description: string
}

const IntegrationsPage: FC = () => {
  const match = useRouteMatch<RouteParams>()
  useEffect(() => {
    API.trackPage(Constants.pages.INTEGRATIONS)
  }, [])

  const integrations = Object.keys(Utils.getIntegrationData())
  const { isLoading: permissionsLoading, permission } = useHasPermission({
    id: match.params.projectId,
    level: 'project',
    permission: 'ADMIN',
  })
  const { data: project } = useGetProjectQuery({ id: match.params.projectId })
  return (
    <div className='app-container container'>
      <PageTitle title={'Integrations'}>
        Enhance Flagsmith with your favourite tools. Have any products you want
        to see us integrate with? Message us and we will be right with you.
      </PageTitle>
      {
        <InfoMessage collapseId='project-integrations'>
          You can also set{' '}
          <Link
            to={`/organisation/${
              AccountStore.getOrganisation()?.id
            }/integrations`}
          >
            Organisation Integrations
          </Link>
          . If you add any of the same integrations here, they will override the
          ones set at the organization level.
        </InfoMessage>
      }

      {permissionsLoading ? (
        <Loader />
      ) : (
        <div>
          <div>
            {permission ? (
              <div>
                {project && (
                  <IntegrationList
                    projectId={match.params.projectId}
                    integrations={integrations}
                  />
                )}
              </div>
            ) : (
              <div>{Constants.projectPermissions('Admin')}</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default IntegrationsPage
