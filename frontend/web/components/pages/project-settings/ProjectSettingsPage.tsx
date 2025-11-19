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
import { GeneralTab } from './tabs/general-tab'
import { SDKSettingsTab } from './tabs/SDKSettingsTab'
import { PermissionsTab } from './tabs/PermissionsTab'
import { CustomFieldsTab } from './tabs/CustomFieldsTab'
import { ImportTab } from './tabs/ImportTab'

const ProjectSettingsPage = () => {
  const { environmentId, projectId } = useRouteContext()
  const {
    data: project,
    isLoading,
    isUninitialized,
  } = useGetProjectQuery({ id: String(projectId) }, { skip: !projectId })

  useEffect(() => {
    API.trackPage(Constants.pages.PROJECT_SETTINGS)
  }, [])

  // Show loader only on initial load (not during refetches from mutations)
  const isInitialLoading = isUninitialized || (isLoading && !project)

  if (isInitialLoading) {
    return (
      <div className='app-container container'>
        <PageTitle title='Project Settings' />
        <div className='text-center'>
          <Loader />
        </div>
      </div>
    )
  }

  const hasEnvironments = !!project?.environments?.length
  const hasFeatureHealth = Utils.getFlagsmithHasFeature('feature_health')

  // Derive organisationId from project data (not available in route params)
  const organisationId = project?.organisation

  if (!project || !projectId || !organisationId) {
    return (
      <div className='app-container container'>
        <PageTitle title='Project Settings' />
        <div className='text-center'>
          <Loader />
        </div>
      </div>
    )
  }

  const tabs = [
    {
      component: <GeneralTab project={project} environmentId={environmentId} />,
      isVisible: true,
      key: 'general',
      label: 'General',
    },
    {
      component: <SDKSettingsTab project={project} />,
      isVisible: true,
      key: 'js-sdk-settings',
      label: 'SDK Settings',
    },
    {
      component: <ProjectUsage projectId={String(project.id)} />,
      isVisible: true,
      key: 'usage',
      label: 'Usage',
    },
    {
      component: (
        <EditHealthProvider projectId={project.id} tabClassName='flat-panel' />
      ),
      isVisible: hasFeatureHealth,
      key: 'feature-health-settings',
      label: <BetaFlag flagName='feature_health'>Feature Health</BetaFlag>,
      labelString: 'Feature Health',
    },
    {
      component: (
        <PermissionsTab
          projectId={project.id}
          organisationId={organisationId}
        />
      ),
      isVisible: true,
      key: 'permissions',
      label: 'Permissions',
    },
    {
      component: <CustomFieldsTab organisationId={organisationId} />,
      isVisible: true,
      key: 'custom-fields',
      label: 'Custom Fields',
    },
    {
      component: (
        <ImportTab
          projectId={String(project.id)}
          environmentId={environmentId}
          projectName={project?.name || ''}
        />
      ),
      isVisible: hasEnvironments,
      key: 'js-import-page',
      label: 'Import',
    },
    {
      component: <FeatureExport projectId={String(project.id)} />,
      isVisible: hasEnvironments,
      key: 'export',
      label: 'Export',
    },
  ]

  return (
    <div className='app-container container'>
      <PageTitle title='Project Settings' />
      <Tabs urlParam='tab' className='mt-0' uncontrolled>
        {tabs.map(
          ({ component, isVisible, key, label, labelString }) =>
            isVisible && (
              <TabItem
                key={key}
                tabLabel={label}
                data-test={key}
                tabLabelString={labelString}
              >
                {component}
              </TabItem>
            ),
        )}
      </Tabs>
    </div>
  )
}

export default ProjectSettingsPage
