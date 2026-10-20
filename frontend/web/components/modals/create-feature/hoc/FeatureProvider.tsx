import React, { Component } from 'react'
import FeatureListStore from 'common/stores/feature-list-store'
import ES6Component from 'common/ES6Component'
import { setModalTitle } from 'components/modals/base/ModalDefault'

type SavedToast = {
  changeRequest?: boolean
  createdFlag?: string
  isCreate?: boolean
  updatedChangeRequest?: { id: number }
}

// TODO: Migrate to a custom hook once we move away from Flux stores.
// This class component is necessary because it uses ES6Component/listenTo
// to subscribe to FeatureListStore events, which requires class lifecycle methods.
export default function withFeatureProvider(
  WrappedComponent: React.ComponentType<any>,
) {
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
            const saved = {
              changeRequest,
              createdFlag,
              isCreate,
              updatedChangeRequest,
            }
            if (this.heldToast) {
              this.heldToast.saved = saved
            } else {
              this.showSavedToast(saved)
            }
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
            const newEnvironmentFlag =
              envFlags?.[this.props.projectFlag.id] || {}
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

    // Held while the modal stages dependency changes into the change request,
    // so a partial save does not show as a success.
    heldToast: { saved?: SavedToast } | null = null

    holdSavedToast = () => {
      const held: { saved?: SavedToast } = {}
      this.heldToast = held
      return (show: boolean) => {
        if (this.heldToast === held) this.heldToast = null
        if (show && held.saved) this.showSavedToast(held.saved)
      }
    }

    showSavedToast = ({
      changeRequest,
      createdFlag,
      isCreate,
      updatedChangeRequest,
    }: SavedToast) => {
      const isEditingChangeRequest = this.props.changeRequest && changeRequest
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

    render() {
      return (
        <WrappedComponent
          key={this.state.projectFlag?.id || 'new'}
          {...this.state}
          holdSavedToast={this.holdSavedToast}
        />
      )
    }
  }

  return FeatureProvider
}
