// import propTypes from 'prop-types';
import React, { Component } from 'react'
import TabItem from 'components/base/forms/TabItem'
import Tabs from 'components/base/forms/Tabs'
import CompareEnvironments from 'components/CompareEnvironments'
import CompareFeatures from 'components/CompareFeatures'
import ConfigProvider from 'common/providers/ConfigProvider'
import CompareIdentities from 'components/CompareIdentities'
import PageTitle from 'components/PageTitle'

class TheComponent extends Component {
  static displayName = 'TheComponent'

  static propTypes = {}

  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  constructor(props) {
    super(props)
  }

  render() {
    return (
      <div className='app-container container'>
        <PageTitle className='mb-2' title={'Compare'}>
          Compare data across your environments, features and identities.
        </PageTitle>
        <Tabs className='mt-0' urlParam='tab'>
          <TabItem tabLabel='Environments'>
            <div className='mt-4'>
              <CompareEnvironments
                projectId={this.props.match.params.projectId}
                environmentId={this.props.match.params.environmentId}
              />
            </div>
          </TabItem>
          <TabItem tabLabel='Feature Values'>
            <div className='mt-4'>
              <CompareFeatures projectId={this.props.match.params.projectId} />
            </div>
          </TabItem>
          <TabItem tabLabel='Identities'>
            <div className='mt-4'>
              <CompareIdentities
                environmentId={this.props.match.params.environmentId}
                projectId={this.props.match.params.projectId}
              />
            </div>
          </TabItem>
        </Tabs>
      </div>
    )
  }
}

module.exports = ConfigProvider(TheComponent)
