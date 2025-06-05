import React, { useEffect } from 'react'
import IntegrationList from 'components/IntegrationList'
import Constants from 'common/constants'
import PageTitle from 'components/PageTitle'
import Utils from 'common/utils/utils'
import InfoMessage from 'components/InfoMessage'
import AccountStore from 'common/stores/account-store'

const OrganisationIntegrationsPage = ({ match }) => {
  useEffect(() => {
    API.trackPage(Constants.pages.INTEGRATIONS)
  }, [])

  const integrationData = Utils.getIntegrationData()
  const integrations = Object.keys(integrationData).filter(
    (v) => !!integrationData[v]?.organisation,
  )
  if (!AccountStore.isAdmin()) {
    return (
      <div
        dangerouslySetInnerHTML={{
          __html: Constants.organisationPermissions('Admin'),
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
      <InfoMessage collapseId='organisation-integrations'>
        You can add more integrations at the project level. If you add the same
        integrations there, they will replace the ones set at the organization
        level.
      </InfoMessage>
      <IntegrationList
        organisationId={Utils.getOrganisationIdFromUrl(match)}
        integrations={integrations}
      />
    </div>
  )
}

export default OrganisationIntegrationsPage
