import React, { Component } from 'react'
import IntegrationList from 'components/IntegrationList'
import Permission from 'common/providers/Permission'
import Constants from 'common/constants'
import PageTitle from 'components/PageTitle'
import Utils from 'common/utils/utils'
import { IntegrationData } from 'common/types/responses'

const OrganisationIntegrationsPage = class extends Component {
  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  constructor(props, context) {
    super(props, context)
    this.state = {}
  }

  componentDidMount = () => {
    API.trackPage(Constants.pages.INTEGRATIONS)
  }

  render() {
    const integrationData = Utils.getIntegrationData()
    const integrations = Object.keys(integrationData).filter(
      (v) => !!integrationData[v]?.organisation,
    )
    return (
      <div className='app-container container'>
        <PageTitle title={'Integrations'}>
          Enhance Flagsmith with your favourite tools. Have any products you
          want to see us integrate with? Message us and we will be right with
          you.
        </PageTitle>
        <IntegrationList
          organisationId={this.props.match.params.organisationId}
          integrations={integrations}
        />
      </div>
    )
  }
}
export default OrganisationIntegrationsPage
