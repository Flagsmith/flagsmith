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
