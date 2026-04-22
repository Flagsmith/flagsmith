import React, { useEffect } from 'react'
import IntegrationList from 'components/IntegrationList'
import Constants from 'common/constants'
import PageTitle from 'components/PageTitle'
import Utils from 'common/utils/utils'
import AccountStore from 'common/stores/account-store'
import { OrganisationPermission } from 'common/types/permissions.types'
import { useHasPermission } from 'common/providers/Permission'
import API from 'project/api'

const OrganisationIntegrationsPage = ({ match }) => {
  useEffect(() => {
    API.trackPage(Constants.pages.INTEGRATIONS)
  }, [])

  const integrationData = Utils.getIntegrationData()
  const allIntegrations = Object.keys(integrationData)
  const orgIntegrations = allIntegrations.filter(
    (key) => !!integrationData[key]?.organisation,
  )
  const projectIntegrations = allIntegrations.filter(
    (key) => !integrationData[key]?.organisation,
  )
  const organisationId = Utils.getOrganisationIdFromUrl(match)
  const { permission: isOrgAdmin } = useHasPermission({
    id: organisationId,
    level: 'organisation',
    permission: OrganisationPermission.ADMIN,
  })
  if (!AccountStore.isAdmin()) {
    return (
      <div
        dangerouslySetInnerHTML={{
          __html: Constants.organisationPermissions(
            OrganisationPermission.ADMIN,
          ),
        }}
        className='text-center'
      ></div>
    )
  }
  return (
    <div className='app-container container'>
      <PageTitle title={'Organisation Integrations'}>
        Enhance Flagsmith with your favourite tools. Have any products you want
        to see us integrate with? Message us and we will be right with you.
      </PageTitle>
      <IntegrationList
        organisationId={organisationId}
        integrations={orgIntegrations}
        isOrgAdmin={isOrgAdmin}
      />
      {!!projectIntegrations.length && (
        <>
          <h5 className='mt-5 mb-3'>Project-level integrations</h5>
          <IntegrationList
            organisationId={organisationId}
            integrations={projectIntegrations}
            isOrgAdmin={isOrgAdmin}
          />
        </>
      )}
    </div>
  )
}

export default OrganisationIntegrationsPage
