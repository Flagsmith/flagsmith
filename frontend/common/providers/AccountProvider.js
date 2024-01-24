import React, { Component } from 'react'
import AccountStore from 'common/stores/account-store'
import AppLoader from 'components/AppLoader'

const AccountProvider = class extends Component {
  static displayName = 'AccountProvider'

  constructor(props, context) {
    super(props, context)
    this.state = {
      isLoading: AccountStore.isLoading,
      organisation: AccountStore.getOrganisation(),
      organisations: AccountStore.getOrganisations(),
      user: AccountStore.getUser(),
    }
  }

  componentDidMount() {
    ES6Component(this)
    this.listenTo(AccountStore, 'change', () => {
      this.setState({
        error: AccountStore.error,
        isLoading: AccountStore.isLoading,
        isSaving: AccountStore.isSaving,
        organisation: AccountStore.getOrganisation(),
        organisations: AccountStore.getOrganisations(),
        user: AccountStore.getUser(),
      })
      this.props.onChange && this.props.onChange()
    })

    this.listenTo(AccountStore, 'loaded', () => {
      this.props.onLogin && this.props.onLogin()
    })

    this.listenTo(AccountStore, 'saved', () => {
      this.props.onSave && this.props.onSave(AccountStore.savedId)
    })

    this.listenTo(AccountStore, 'logout', () => {
      this.setState({
        isLoading: false,
        isSaving: false,
        organisation: AccountStore.getOrganisation(),
        user: AccountStore.getUser(),
      })
      this.props.onLogout && this.props.onLogout()
    })
    this.listenTo(AccountStore, 'no-user', () => {
      this.setState({
        isLoading: false,
        isSaving: false,
        organisation: AccountStore.getOrganisation(),
        user: AccountStore.getUser(),
      })
      this.props.onNoUser && this.props.onNoUser()
    })
    this.listenTo(AccountStore, 'problem', () => {
      this.setState({
        error: AccountStore.error,
        isLoading: AccountStore.isLoading,
        isSaving: AccountStore.isSaving,
      })
    })
    this.listenTo(AccountStore, 'removed', () => {
      this.props.onRemove && this.props.onRemove()
      if (this.props.onLogin) {
        this.setState({
          isLoading: false,
          isSaving: false,
          organisation: AccountStore.getOrganisation(),
          user: AccountStore.getUser(),
        })
      }
    })
  }

  login = (details) => {
    AppActions.login(details)
  }
  register = (details, isInvite) => {
    AppActions.register(details, isInvite)
  }

  render() {
    const { error, isLoading, isSaving, organisation, organisations, user } =
      this.state
    if (isLoading) {
      return <AppLoader />
    }
    return this.props.children(
      {
        error,
        isLoading,
        isSaving,
        organisation,
        organisations,
        user,
      },
      {
        acceptInvite: AppActions.acceptInvite,
        confirmTwoFactor: AppActions.confirmTwoFactor,
        createOrganisation: AppActions.createOrganisation,
        deleteOrganisation: AppActions.deleteOrganisation,
        disableTwoFactor: AppActions.disableTwoFactor,
        editOrganisation: AppActions.editOrganisation,
        enableTwoFactor: AppActions.enableTwoFactor,
        login: this.login,
        register: this.register,
        selectOrganisation: AppActions.selectOrganisation,
        twoFactorLogin: AppActions.twoFactorLogin,
      },
    )
  }
}

AccountProvider.propTypes = {
  children: OptionalFunc,
  onChange: OptionalFunc,
  onLogin: OptionalFunc,
  onLogout: OptionalFunc,
  onNoUser: OptionalFunc,
  onRemove: OptionalFunc,
  onSave: OptionalFunc,
}

export default AccountProvider
