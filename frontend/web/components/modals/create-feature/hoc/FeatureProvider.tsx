import React, { Component } from 'react'
import FeatureListStore from 'common/stores/feature-list-store'
import ES6Component from 'common/ES6Component'
import ConfigProvider from 'common/providers/ConfigProvider'
import withSegmentOverrides from 'common/providers/withSegmentOverrides'
import { setModalTitle } from 'components/modals/base/ModalDefault'
import CreateFeatureModal from './..'

// TODO: Migrate to a custom hook once we move away from Flux stores.
// This class component is necessary because it uses ES6Component/listenTo
// to subscribe to FeatureListStore events, which requires class lifecycle methods.
const WrappedCreateFlag = ConfigProvider(
  withSegmentOverrides(CreateFeatureModal),
)

class FeatureProvider extends Component<any, any> {
  constructor(props: any) {
    super(props)
    this.state = {
      ...props,
    }
    ES6Component(this)
  }

  componentDidMount() {
    ES6Component(this)
    this.listenTo(
      FeatureListStore,
      'saved',
      ({
        changeRequest,
        createdFlag,
        error,
        isCreate,
        updatedChangeRequest,
      }: any = {}) => {
        if (error?.data?.metadata) {
          error.data.metadata?.forEach((m: any) => {
            if (Object.keys(m).length > 0) {
              toast(m.non_field_errors[0], 'danger')
            }
          })
        } else if (error?.data) {
          toast('Error updating the Flag', 'danger')
          return
        } else {
          const isEditingChangeRequest =
            this.props.changeRequest && changeRequest
          const operation = createdFlag || isCreate ? 'Created' : 'Updated'
          const type = changeRequest ? 'Change Request' : 'Feature'

          const toastText = isEditingChangeRequest
            ? `Updated ${type}`
            : `${operation} ${type}`
          const toastAction = changeRequest
            ? {
                buttonText: 'Open',
                onClick: () => {
                  closeModal()
                  this.props.history.push(
                    `/project/${this.props.projectId}/environment/${this.props.environmentId}/change-requests/${updatedChangeRequest?.id}`,
                  )
                },
              }
            : undefined

          toast(toastText, 'success', undefined, toastAction)
        }
        const envFlags = FeatureListStore.getEnvironmentFlags()

        if (createdFlag) {
          const projectFlag = FeatureListStore.getProjectFlags()?.find?.(
            (flag: any) => flag.name === createdFlag,
          )
          window.history.replaceState(
            {},
            `${document.location.pathname}?feature=${projectFlag.id}`,
          )
          const newEnvironmentFlag = envFlags?.[projectFlag.id] || {}
          setModalTitle(`Edit Feature ${projectFlag.name}`)
          this.setState({
            environmentFlag: {
              ...this.state.environmentFlag,
              ...(newEnvironmentFlag || {}),
            },
            projectFlag,
            segmentsChanged: false,
            settingsChanged: false,
            valueChanged: false,
          })
        } else if (this.props.projectFlag) {
          const newEnvironmentFlag = envFlags?.[this.props.projectFlag.id] || {}
          const newProjectFlag = FeatureListStore.getProjectFlags()?.find?.(
            (flag: any) => flag.id === this.props.projectFlag.id,
          )
          this.setState({
            environmentFlag: {
              ...this.state.environmentFlag,
              ...(newEnvironmentFlag || {}),
            },
            projectFlag: newProjectFlag,
            segmentsChanged: false,
            settingsChanged: false,
            valueChanged: false,
          })
        }
      },
    )
  }

  listenTo: any

  render() {
    return (
      <WrappedCreateFlag
        key={this.state.projectFlag?.id || 'new'}
        {...this.state}
      />
    )
  }
}

export default FeatureProvider
