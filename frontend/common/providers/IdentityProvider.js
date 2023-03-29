import React from 'react'
import FeatureListStore from 'common/stores/feature-list-store'
import IdentityStore from 'common/stores/identity-store'

const IdentityProvider = class extends React.Component {
  static displayName = 'IdentityProvider'

  constructor(props, context) {
    super(props, context)
    this.state = {
      environmentFlags: FeatureListStore.getEnvironmentFlags(),
      identity: IdentityStore.model,
      identityFlags: IdentityStore.getIdentityFlags(),
      isLoading: true,
      projectFlags: FeatureListStore.getProjectFlags(),
    }
    ES6Component(this)
  }

  componentDidMount() {
    this.listenTo(IdentityStore, 'change', () => {
      this.setState({
        identity: IdentityStore.model,
        identityFlags: IdentityStore.getIdentityFlags(),
        isLoading: IdentityStore.isLoading || FeatureListStore.isLoading,
        isSaving: IdentityStore.isSaving,
        traits: IdentityStore.getTraits(),
      })
    })
    this.listenTo(FeatureListStore, 'change', () => {
      this.setState({
        environmentFlags: FeatureListStore.getEnvironmentFlags(),
        isLoading: IdentityStore.isLoading || FeatureListStore.isLoading,
        projectFlags: FeatureListStore.getProjectFlags(),
      })
    })

    this.listenTo(IdentityStore, 'saved', () => {
      this.props.onSave && this.props.onSave()
    })
  }

  toggleFlag = ({
    environmentFlag,
    environmentId,
    identity,
    identityFlag,
    projectFlag,
  }) => {
    AppActions.toggleUserFlag({
      environmentFlag,
      environmentId,
      identity,
      identityFlag,
      projectFlag,
    })
  }

  editFeatureValue = ({
    environmentFlag,
    environmentId,
    identity,
    identityFlag,
    projectFlag,
  }) => {
    AppActions.editUserFlag({
      environmentFlag,
      environmentId,
      identity,
      identityFlag,
      projectFlag,
    })
  }

  editTrait = ({ environmentId, identity, trait }) => {
    AppActions.editTrait({ environmentId, identity, trait })
  }

  createTrait = ({ environmentId, identity, isCreate, trait }) => {
    AppActions.editTrait({ environmentId, identity, isCreate, trait })
  }

  removeFlag = ({ environmentId, identity, identityFlag }) => {
    AppActions.removeUserFlag({ environmentId, identity, identityFlag })
  }

  changeUserFlag = ({ environmentId, identity, identityFlag, payload }) => {
    AppActions.changeUserFlag({
      environmentId,
      identity,
      identityFlag,
      payload,
    })
  }

  render() {
    const {
      changeUserFlag,
      createTrait,
      editFeatureValue,
      editTrait,
      removeFlag,
      toggleFlag,
    } = this
    return this.props.children(
      { ...this.state },
      {
        changeUserFlag,
        createTrait,
        editFeatureValue,
        editTrait,
        removeFlag,
        toggleFlag,
      },
    )
  }
}

IdentityProvider.propTypes = {
  children: OptionalFunc,
  onSave: OptionalFunc,
}

module.exports = IdentityProvider
