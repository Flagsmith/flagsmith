// import propTypes from 'prop-types';
import React, { Component } from 'react'
import TabItem from 'components/base/forms/TabItem'
import Tabs from 'components/base/forms/Tabs'
import CompareEnvironments from 'components/CompareEnvironments'
import CompareFeatures from 'components/CompareFeatures'
import ConfigProvider from 'common/providers/ConfigProvider'

class TheComponent extends Component {
  static displayName = 'TheComponent'

  static propTypes = {}

  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  constructor(props) {
    super()
    this.state = {
      tab: 0,
    }
  }

  render() {
    return (
      <div className='app-container container'>
        <Tabs
          value={this.state.tab}
          onChange={(tab) => {
            this.setState({ tab })
          }}
        >
          <TabItem tabLabel='Environments'>
            <div className='mt-2'>
              <CompareEnvironments
                projectId={this.props.match.params.projectId}
                environmentId={this.props.match.params.environmentId}
              />
            </div>
          </TabItem>
          <TabItem tabLabel='Feature Values'>
            <div className='mt-2'>
              <CompareFeatures projectId={this.props.match.params.projectId} />
            </div>
          </TabItem>
        </Tabs>
      </div>
    )
  }
}

module.exports = ConfigProvider(TheComponent)
