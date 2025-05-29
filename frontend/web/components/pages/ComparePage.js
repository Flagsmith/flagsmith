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
import Utils from 'common/utils/utils'
class ComparePage extends Component {
  static displayName = 'ComparePage'

  static propTypes = {}

  constructor(props) {
    super(props)
  }

  render() {
    const projectIdFromUrl = Utils.getProjectIdFromUrl(this.props.match)
    return (
      <div className='app-container container'>
        <PageTitle className='mb-2' title={'Compare'}>
          Compare data across your environments, features and identities.
        </PageTitle>
        <Tabs className='mt-0' urlParam='tab' history={this.props.history}>
          <TabItem tabLabel='Environments'>
            <div className='mt-4'>
              <CompareEnvironments
                projectId={projectIdFromUrl}
                environmentId={this.props.match.params.environmentId}
              />
            </div>
          </TabItem>
          <TabItem tabLabel='Feature Values'>
            <div className='mt-4'>
              <CompareFeatures projectId={projectIdFromUrl} />
            </div>
          </TabItem>
          <TabItem tabLabel='Identities'>
            <div className='mt-4'>
              <CompareIdentities
                environmentId={this.props.match.params.environmentId}
                projectId={projectIdFromUrl}
              />
            </div>
          </TabItem>
        </Tabs>
      </div>
    )
  }
}

module.exports = withRouter(ConfigProvider(ComparePage))
