import React, { Component } from 'react'
import flagsmith from 'flagsmith'
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
    }

    render() {
      const { error, isLoading } = this.state
      const { getValue, hasFeature } = flagsmith

      return (
        <WrappedComponent
          ref='wrappedComponent'
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
