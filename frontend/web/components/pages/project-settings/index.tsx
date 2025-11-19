import React, { useEffect } from 'react'
import PageTitle from 'components/PageTitle'
import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'
import BetaFlag from 'components/BetaFlag'
import { useGetProjectQuery } from 'common/services/useProject'
import { useRouteContext } from 'components/providers/RouteContext'
import Constants from 'common/constants'
import Utils from 'common/utils/utils'
import ProjectUsage from 'components/ProjectUsage'
import EditHealthProvider from 'components/EditHealthProvider'
import FeatureExport from 'components/import-export/FeatureExport'
import { GeneralTab } from './tabs/GeneralTab'
import { SDKSettingsTab } from './tabs/SDKSettingsTab'
import { PermissionsTab } from './tabs/PermissionsTab'
import { CustomFieldsTab } from './tabs/CustomFieldsTab'
import { ImportTab } from './tabs/ImportTab'

const ProjectSettingsPage = () => {
  const { environmentId, organisationId, projectId } = useRouteContext()
  const { data: project, isLoading } = useGetProjectQuery(
    { id: String(projectId) },
    { skip: !projectId },
  )

  useEffect(() => {
    API.trackPage(Constants.pages.PROJECT_SETTINGS)
  }, [])

  const hasEnvironments = !!project?.environments?.length
  const hasFeatureHealth = Utils.getFlagsmithHasFeature('feature_health')

  if (isLoading || !project || !projectId) {
    return (
      <div className='app-container container'>
        <PageTitle title='Project Settings' />
        <div className='text-center'>
          <Loader />
        </div>
      </div>
    )
  }

  return (
    <div className='app-container container'>
      <PageTitle title='Project Settings' />
      <Tabs urlParam='tab' className='mt-0' uncontrolled>
        <TabItem tabLabel='General'>
          <GeneralTab
            project={project}
            projectId={projectId}
            environmentId={environmentId}
            organisationId={organisationId}
          />
        </TabItem>

        <TabItem data-test='js-sdk-settings' tabLabel='SDK Settings'>
          <SDKSettingsTab
            project={project}
            projectId={projectId}
            environmentId={environmentId}
            organisationId={organisationId}
          />
        </TabItem>

        <TabItem tabLabel='Usage'>
          <ProjectUsage projectId={String(projectId)} />
        </TabItem>

        {hasFeatureHealth && (
          <TabItem
            data-test='feature-health-settings'
            tabLabel={
              <BetaFlag flagName='feature_health'>Feature Health</BetaFlag>
            }
            tabLabelString='Feature Health'
          >
            <EditHealthProvider
              projectId={projectId}
              tabClassName='flat-panel'
            />
          </TabItem>
        )}

        <TabItem tabLabel='Permissions'>
          <PermissionsTab
            projectId={projectId}
            environmentId={environmentId}
            organisationId={organisationId}
          />
        </TabItem>

        <TabItem tabLabel='Custom Fields'>
          <CustomFieldsTab
            projectId={projectId}
            environmentId={environmentId}
            organisationId={organisationId}
          />
        </TabItem>

        {hasEnvironments && (
          <TabItem data-test='js-import-page' tabLabel='Import'>
            <ImportTab
              projectId={projectId}
              environmentId={environmentId}
              organisationId={organisationId}
            />
          </TabItem>
        )}

        {hasEnvironments && (
          <TabItem tabLabel='Export'>
            <FeatureExport projectId={String(projectId)} />
          </TabItem>
        )}
      </Tabs>
    </div>
  )
}

export default ProjectSettingsPage
