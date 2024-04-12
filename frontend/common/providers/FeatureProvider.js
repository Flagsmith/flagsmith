//This will remount the modal when a feature is created
import FeatureListStore from 'common/stores/feature-list-store'
import { setModalTitle } from 'components/modals/base/ModalDefault'
import { Component } from 'react'

const FeatureProvider = (WrappedComponent) => {
  class HOC extends Component {
    static contextTypes = {
      router: propTypes.object.isRequired,
    }

    constructor(props) {
      super(props)
      this.state = {
        ...props,
      }
      ES6Component(this)
    }

    componentDidMount() {
      ES6Component(this)
      this.listenTo(FeatureListStore, 'saved', (createdFlag) => {
        if (createdFlag) {
          const projectFlag = FeatureListStore.getProjectFlags()?.find?.(
            (flag) => flag.name === createdFlag,
          )
          window.history.replaceState(
            {},
            `${document.location.pathname}?feature=${projectFlag.id}`,
          )
          const envFlags = FeatureListStore.getEnvironmentFlags()
          const newEnvironmentFlag = envFlags?.[projectFlag.id] || {}
          setModalTitle(`Edit Feature ${projectFlag.name}`)
          this.setState({
            environmentFlag: {
              ...this.state.environmentFlag,
              ...(newEnvironmentFlag || {}),
            },
            projectFlag,
          })
        }
      })
    }

    render() {
      return (
        <WrappedComponent
          key={this.state.projectFlag?.id || 'new'}
          {...this.state}
        />
      )
    }
  }
  return HOC
}

export default FeatureProvider
