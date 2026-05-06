import React from 'react'
import Utils from 'common/utils/utils'
import Constants from 'common/constants'
import API from 'project/api'
import CreateEditIntegration from 'components/modals/CreateEditIntegrationModal'
import { IntegrationData } from 'common/types/responses'

type OpenIntegrationOptions = {
  projectId?: string
  organisationId?: string
}

export const openIntegrationModal = (
  key: string,
  options: OpenIntegrationOptions = {},
) => {
  const integrationData = Utils.getIntegrationData() as
    | Record<string, IntegrationData>
    | null
    | undefined
  const integration = integrationData?.[key]
  if (!integration) return
  API.trackEvent(Constants.events.VIEW_INTEGRATION(key))
  // External-installation integrations (e.g. GitHub) need a child-window
  // OAuth flow before the side modal can render anything useful. Open the
  // integrations page in a new tab so the user can run the install flow
  // without losing context in the current modal.
  if (integration.isExternalInstallation && options.projectId) {
    window.open(
      `/project/${options.projectId}/integrations?configure=${key}`,
      '_blank',
      'noreferrer',
    )
    return
  }
  openModal(
    `${integration.title || key} Integration`,
    <CreateEditIntegration
      id={key}
      modal
      integration={integration}
      organisationId={options.organisationId}
      projectId={options.projectId}
    />,
    'side-modal',
  )
}
