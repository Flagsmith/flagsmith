import React, { Component } from 'react'
import flagsmith from '@flagsmith/flagsmith'
import ConfigStore from 'common/stores/config-store'

export default (WrappedComponent) => {
  class HOC extends Component {
    constructor(props) {
      super(props)
      this.state = {
        error: ConfigStore.error,
        isLoading: ConfigStore.model ? ConfigStore.isLoading : true,
      }
      ES6Component(this)
    }

    componentDidMount() {
      this.listenTo(ConfigStore, 'change', () => {
        this.setState({
          error: ConfigStore.error,
          isLoading: ConfigStore.isLoading,
        })
      })
      // The SDK's onChange can fire in the gap between the constructor
      // reading the store and this subscription. With realtime and events
      // disabled (E2E) no further change event arrives, so a missed one
      // leaves the app on the loader forever — re-sync after subscribing.
      if (ConfigStore.model || ConfigStore.error) {
        this.setState({
          error: ConfigStore.error,
          isLoading: ConfigStore.isLoading,
        })
      }
    }

    render() {
      const { error, isLoading } = this.state
      const { getValue, hasFeature } = flagsmith

      return (
        <WrappedComponent
          isLoading={isLoading}
          error={error}
          history={this.props.history}
          {...this.props}
          getValue={getValue}
          hasFeature={hasFeature}
        />
      )
    }
  }

  return HOC
}
