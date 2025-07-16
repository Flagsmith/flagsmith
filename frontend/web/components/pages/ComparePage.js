// import propTypes from 'prop-types';
import React, { Component } from 'react'
import TabItem from 'components/base/forms/TabItem'
import Tabs from 'components/base/forms/Tabs'
import CompareEnvironments from 'components/CompareEnvironments'
import CompareFeatures from 'components/CompareFeatures'
import ConfigProvider from 'common/providers/ConfigProvider'
import CompareIdentities from 'components/CompareIdentities'
import PageTitle from 'components/PageTitle'
import { withRouter } from 'react-router-dom'
import {
  RouteContext,
  useRouteContext,
} from 'components/providers/RouteContext'

class ComparePage extends Component {
  static contextType = RouteContext
  static displayName = 'ComparePage'

  static propTypes = {}

  constructor(props) {
    super(props)
    this.projectId = props.routeContext.projectId
  }

  render() {
    return (
      <div className='app-container container'>
        <PageTitle className='mb-2' title={'Compare'}>
          Compare data across your environments, features and identities.
        </PageTitle>
        <Tabs className='mt-0' urlParam='tab' history={this.props.history}>
          <TabItem tabLabel='Environments'>
            <div className='mt-4'>
              <CompareEnvironments
                projectId={this.projectId}
                environmentId={this.props.match.params.environmentId}
              />
            </div>
          </TabItem>
          <TabItem tabLabel='Feature Values'>
            <div className='mt-4'>
              <CompareFeatures projectId={this.projectId} />
            </div>
          </TabItem>
          <TabItem tabLabel='Identities'>
            <div className='mt-4'>
              <CompareIdentities
                environmentId={this.props.match.params.environmentId}
                projectId={this.projectId}
              />
            </div>
          </TabItem>
        </Tabs>
      </div>
    )
  }
}

const ComparePageWithContext = (props) => {
  const context = useRouteContext()
  return <ComparePage {...props} routeContext={context} />
}

module.exports = withRouter(ConfigProvider(ComparePageWithContext))
