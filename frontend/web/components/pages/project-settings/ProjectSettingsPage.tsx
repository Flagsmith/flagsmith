import React, { ReactNode, useEffect } from 'react'
import PageTitle from 'components/PageTitle'
import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'
import BetaFlag from 'components/BetaFlag'
import { useGetProjectQuery } from 'common/services/useProject'
import { useRouteContext } from 'components/providers/RouteContext'
import Constants from 'common/constants'
import Utils from 'common/utils/utils'
import ProjectUsage from 'components/ProjectUsage'
import EditHealthProvider from './tabs/EditHealthProvider'
import FeatureExport from 'components/import-export/FeatureExport'
import { GeneralTab } from './tabs/general-tab'
import { SDKSettingsTab } from './tabs/SDKSettingsTab'
import { PermissionsTab } from './tabs/PermissionsTab'
import { CustomFieldsTab } from './tabs/CustomFieldsTab'
import { ImportTab } from './tabs/ImportTab'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'

type ProjectSettingsTab = {
  component: ReactNode
  isVisible: boolean
  key: string
  label: ReactNode
  labelString?: string
}

const ProjectSettingsPage = () => {
  const { environmentId, projectId } = useRouteContext()
  const {
    data: project,
    error,
    isLoading,
    isUninitialized,
  } = useGetProjectQuery({ id: projectId! }, { skip: !projectId })
  const { data: environments } = useGetEnvironmentsQuery(
    { projectId: projectId! },
    { skip: !projectId },
  )

  useEffect(() => {
    API.trackPage(Constants.pages.PROJECT_SETTINGS)
  }, [])

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

  if (error || !project || !projectId || !project?.organisation) {
    return (
      <div className='app-container container'>
        <PageTitle title='Project Settings' />
        <div className='alert alert-danger mt-4 text-center'>
          Failed to load project settings. Please try again.
        </div>
      </div>
    )
  }

  // Derive data from project after all early returns
  const hasEnvironments = (environments?.results?.length || 0) > 0
  const hasFeatureHealth = Utils.getFlagsmithHasFeature('feature_health')
  const organisationId = project.organisation

  const tabs: ProjectSettingsTab[] = [
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
  ].filter(({ isVisible }) => isVisible)

  return (
    <div className='app-container container'>
      <PageTitle title='Project Settings' />
      <Tabs urlParam='tab' className='mt-0' uncontrolled>
        {tabs.map(({ component, key, label, labelString }) => (
          <TabItem
            key={key}
            tabLabel={label}
            data-test={key}
            tabLabelString={labelString}
          >
            {component}
          </TabItem>
        ))}
      </Tabs>
    </div>
  )
}

export default ProjectSettingsPage
