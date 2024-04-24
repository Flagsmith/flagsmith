const Dispatcher = require('../dispatcher/dispatcher')
const BaseStore = require('./base/_store')
const data = require('../data/base/_data')
import Constants from 'common/constants'
import dataRelay from 'data-relay'
import { sortBy } from 'lodash'

const controller = {
  acceptInvite: (id) => {
    store.saving()
    API.setInvite('')
    API.setInviteType('')
    return data
      .post(`${Project.api}users/join/link/${id}/`)
      .catch((error) => {
        if (
          Utils.getFlagsmithHasFeature('verify_seats_limit_for_invite_links') &&
          error.status === 400
        ) {
          API.ajaxHandler(store, error)
          return
        }
        return data.post(`${Project.api}users/join/${id}/`)
      })
      .then((res) => {
        store.savedId = res.id
        store.model.organisations.push(res)
        const ev = Constants.events.ACCEPT_INVITE(res.name)
        API.postEvent(
          ev.event + (ev.extra ? ` ${ev.extra}` : ''),
          'first_events',
        )
          .catch(() => {})
          .finally(() => {
            AsyncStorage.setItem('user', JSON.stringify(store.model))
            store.saved()
          })
      })
      .catch((e) => {
        API.ajaxHandler(store, e)
      })
  },
  confirmTwoFactor: (pin, onError, isLoginPage) => {
    store.saving()

    return data
      .post(`${Project.api}auth/app/activate/confirm/`, { code: pin })
      .then((res) => {
        store.model.backupCodes = res.backup_codes
        store.model.twoFactorEnabled = true
        store.model.twoFactorConfirmed = true

        store.saved()
        if (isLoginPage) {
          window.location.href = `/organisation-settings`
        }
      })
      .catch((e) => {
        if (onError) {
          onError()
        }
        API.ajaxHandler(store, e)
      })
  },
  createOrganisation: (name) => {
    store.saving()
    if (
      !AccountStore.model.organisations ||
      !AccountStore.model.organisations.length
    ) {
      API.trackEvent(Constants.events.CREATE_FIRST_ORGANISATION)
    }
    API.trackEvent(Constants.events.CREATE_ORGANISATION)
    if (API.getReferrer()) {
      // eslint-disable-next-line camelcase
      API.postEvent(`${name} from ${`${API.getReferrer().utm_source}`}`)
      API.trackEvent(
        Constants.events.REFERRER_CONVERSION(API.getReferrer().utm_source),
      )
    } else {
      // eslint-disable-next-line camelcase
      API.postEvent(`${name}`)
    }

    data.post(`${Project.api}organisations/`, { name }).then((res) => {
      store.model.organisations = store.model.organisations.concat([
        { ...res, role: 'ADMIN' },
      ])
      AsyncStorage.setItem('user', JSON.stringify(store.model))
      store.savedId = res.id
      store.saved()

      const relayEventKey = Utils.getFlagsmithValue('relay_events_key')
      const sendRelayEvent =
        Utils.getFlagsmithHasFeature('relay_events_key') && !!relayEventKey
      if (sendRelayEvent) {
        dataRelay.sendEvent(AccountStore.getUser(), {
          apiKey: relayEventKey,
        })
      }
    })
  },
  deleteOrganisation: () => {
    API.trackEvent(Constants.events.DELETE_ORGANISATION)
    data
      .delete(`${Project.api}organisations/${store.organisation.id}/`)
      .then(() => {
        store.model.organisations = _.filter(
          store.model.organisations,
          (org) => org.id !== store.organisation.id,
        )
        store.organisation = store.model.organisations.length
          ? store.model.organisations[0]
          : null
        store.trigger('removed')
        AsyncStorage.setItem('user', JSON.stringify(store.model))
      })
  },
  disableTwoFactor: () => {
    store.saving()
    return data.post(`${Project.api}auth/app/deactivate/`).then(() => {
      store.model.twoFactorEnabled = false
      store.model.twoFactorConfirmed = false
      store.saved()
    })
  },
  editOrganisation: (org) => {
    API.trackEvent(Constants.events.EDIT_ORGANISATION)
    data
      .put(`${Project.api}organisations/${store.organisation.id}/`, org)
      .then((res) => {
        const idx = _.findIndex(store.model.organisations, {
          id: store.organisation.id,
        })
        if (idx !== -1) {
          store.model.organisations[idx] = res
          store.organisation = res
        }
        store.saved()
      })
  },
  enableTwoFactor: () => {
    store.saving()
    return data.post(`${Project.api}auth/app/activate/`).then((res) => {
      store.model.twoFactor = res
      store.model.twoFactorEnabled = true
      store.saved()
    })
  },
  getOrganisations: () =>
    Promise.all([
      data.get(`${Project.api}organisations/`),
      data.get(`${Project.api}auth/users/me/`),
      data.get(`${Project.api}auth/mfa/user-active-methods/`),
    ])
      .then(([res, userRes, methods]) => {
        controller.setUser({
          ...userRes,
          organisations: res.results,
          twoFactorConfirmed: !!methods.length,
          twoFactorEnabled: !!methods.length,
          twoFactorPrompt: store.ephemeral_token && !!methods.length,
        })
      })
      .catch((e) => API.ajaxHandler(store, e)),
  login: ({ email, password }) => {
    store.loading()
    data
      .post(`${Project.api}auth/login/`, {
        email,
        password,
      })
      .then((res) => {
        API.trackEvent(Constants.events.LOGIN)
        store.samlOrOauth = false
        if (res.ephemeral_token) {
          store.ephemeral_token = res.ephemeral_token
          store.model = {
            twoFactorEnabled: true,
            twoFactorPrompt: true,
          }
          store.loaded()
          return
        }

        data.setToken(res.key)
        return controller.onLogin()
      })
      .catch((e) => API.ajaxHandler(store, e))
  },
  oauth: (type, _data) => {
    store.loading()
    API.trackEvent(Constants.events.OAUTH(type))

    data
      .post(
        type === 'saml'
          ? `${Project.api}auth/saml/login/`
          : `${Project.api}auth/oauth/${type}/`,
        {
          ...(_data || {}),
          sign_up_type: API.getInviteType(),
        },
      )
      .then((res) => {
        store.samlOrOauth = true
        if (res.ephemeral_token) {
          store.ephemeral_token = res.ephemeral_token
          store.model = {
            twoFactorEnabled: true,
            twoFactorPrompt: true,
          }
          store.loaded()
          return
        }

        data.setToken(res.key)
        return controller.onLogin()
      })
      .catch((e) => API.ajaxHandler(store, e))
  },
  onLogin: (skipCaching) => {
    if (!skipCaching) {
      API.setCookie('t', data.token)
    }
    return controller.getOrganisations()
  },
  register: ({
    email,
    first_name,
    last_name,
    marketing_consent_given,
    password,
  }) => {
    store.saving()
    data
      .post(`${Project.api}auth/users/`, {
        email,
        first_name,
        last_name,
        marketing_consent_given,
        password,
        referrer: API.getReferrer() || '',
        sign_up_type: API.getInviteType(),
      })
      .then((res) => {
        data.setToken(res.key)
        API.trackEvent(Constants.events.REGISTER)
        if (API.getReferrer()) {
          API.trackEvent(
            Constants.events.REFERRER_REGISTERED(API.getReferrer().utm_source),
          )
        }

        store.isSaving = false
        return controller.onLogin()
      })
      .catch((e) => API.ajaxHandler(store, e))
  },

  resetPassword: (uid, token, new_password1, new_password2) => {
    store.saving()
    data
      .post(`${Project.api}auth/users/reset_password_confirm/`, {
        new_password: new_password1,

        re_new_password: new_password2,

        token,
        // data.post(`${Project.api}auth/password/reset/confirm/`, {
        uid,
      })
      .then(() => {
        store.saved()
      })
      .catch((e) => API.ajaxHandler(store, e))
  },

  selectOrganisation: (id) => {
    store.organisation = _.find(store.model.organisations, { id })
    store.changed()
  },

  setToken: (token) => {
    store.loading()
    store.user = {}

    data.setToken(token)
    return controller.onLogin()
  },

  setUser(user) {
    if (user) {
      const sortedOrganisations = sortBy(user.organisations, (v) => {
        return v.name
      })
      user.organisations = sortedOrganisations
      store.model = user
      if (user && user.organisations) {
        store.organisation = user.organisations[0]
        const cookiedID = API.getCookie('organisation')
        if (cookiedID) {
          const foundOrganisation = user.organisations.find(
            (v) => `${v.id}` === cookiedID,
          )
          if (foundOrganisation) {
            store.organisation = foundOrganisation
          }
        }
      }

      AsyncStorage.setItem('user', JSON.stringify(store.model))
      API.alias(user.email, user)
      API.identify(user && user.email, user)
      store.loaded()
    } else if (!user) {
      store.ephemeral_token = null
      AsyncStorage.clear()
      API.setCookie('t', '')
      data.setToken(null)
      API.reset().finally(() => {
        store.model = user
        store.organisation = null
        store.trigger('logout')
      })
    }
  },

  twoFactorLogin: (pin, onError) => {
    store.saving()
    return data
      .post(`${Project.api}auth/login/code/`, {
        code: pin,
        ephemeral_token: store.ephemeral_token,
      })
      .then((res) => {
        store.model = null
        API.trackEvent(Constants.events.LOGIN)
        data.setToken(res.key)
        store.ephemeral_token = null
        controller.onLogin()
      })
      .catch((e) => {
        if (onError) {
          onError()
        }
        API.ajaxHandler(store, e)
      })
  },

  updateSubscription: (hostedPageId) => {
    data
      .post(
        `${Project.api}organisations/${store.organisation.id}/update-subscription/`,
        { hosted_page_id: hostedPageId },
      )
      .then((res) => {
        const idx = _.findIndex(store.model.organisations, {
          id: store.organisation.id,
        })
        if (idx !== -1) {
          store.model.organisations[idx] = res
          try {
            if (res && res.subscription && res.subscription.plan) {
              API.postEvent(res.subscription.plan, 'chargebee')
            }
          } catch (e) {}
          store.organisation = res
        }
        store.saved()
      })
      .catch((e) => API.ajaxHandler(store, e))
  },
}

const store = Object.assign({}, BaseStore, {
  forced2Factor() {
    if (!store.model || !store.model.organisations) return false

    if (store.model.twoFactorConfirmed) {
      return false
    }

    if (store.samlOrOauth) {
      return false
    }

    return (
      Utils.getFlagsmithHasFeature('force_2fa') &&
      store.getOrganisations() &&
      store.getOrganisations().find((o) => o.force_2fa)
    )
  },
  getActiveOrgPlan() {
    return (
      store.organisation &&
      store.organisation.subscription &&
      store.organisation.subscription.plan
    )
  },
  getDate() {
    return store.getOrganisation() && store.getOrganisation().created_date
  },
  getOrganisation() {
    return store.organisation
  },
  getOrganisationPlan(id) {
    const organisations = store.getOrganisations()
    const organisation = organisations && organisations.find((v) => v.id === id)
    if (organisation) {
      return !!organisation.subscription?.subscription_id
    }
    return null
  },
  getOrganisationRole(id) {
    return (
      store.model &&
      store.model.organisations &&
      _.get(
        _.find(store.model.organisations, (org) =>
          id
            ? org.id === id
            : org.id === (store.organisation && store.organisation.id),
        ),
        'role',
      )
    )
  },
  getOrganisations() {
    return store.model && store.model.organisations
  },
  getPaymentMethod() {
    return store.organisation?.subscription?.payment_method
  },
  getPlans() {
    if (!store.model) return []
    return _.filter(
      store.model.organisations.map(
        (org) => org.subscription && org.subscription.plan,
      ),
      (plan) => !!plan,
    )
  },
  getUser() {
    return store.model
  },
  getUserId() {
    return store.model && store.model.id
  },
  id: 'account',
  isAdmin() {
    const id = store.organisation && store.organisation.id
    return id && store.getOrganisationRole(id) === 'ADMIN'
  },
  isSuper() {
    return store.model && store.model.is_superuser
  },
  setToken(token) {
    data.token = token
  },
  setUser(user) {
    controller.setUser(user)
  },
})

store.dispatcherIndex = Dispatcher.register(store, (payload) => {
  const action = payload.action // this is our action from handleViewAction

  switch (action.actionType) {
    case Actions.SET_USER:
      controller.setUser(action.user)
      break
    case Actions.SET_TOKEN:
      controller.setToken(action.token)
      break
    case Actions.SELECT_ORGANISATION:
      controller.selectOrganisation(action.id)
      break
    case Actions.CREATE_ORGANISATION:
      controller.createOrganisation(action.name)
      break
    case Actions.ACCEPT_INVITE:
      controller.acceptInvite(action.id)
      break
    case Actions.DELETE_ORGANISATION:
      controller.deleteOrganisation()
      break
    case Actions.EDIT_ORGANISATION:
      controller.editOrganisation(action.org)
      break
    case Actions.LOGOUT:
      controller.setUser(null)
      break
    case Actions.REGISTER:
      controller.register(action.details, action.isInvite)
      break
    case Actions.RESET_PASSWORD:
      controller.resetPassword(
        action.uid,
        action.token,
        action.new_password1,
        action.new_password2,
      )
      break
    case Actions.LOGIN:
      controller.login(action.details)
      break
    case Actions.GET_ORGANISATIONS:
      controller.getOrganisations()
      break
    case Actions.ENABLE_TWO_FACTOR:
      controller.enableTwoFactor()
      break
    case Actions.CONFIRM_TWO_FACTOR:
      controller.confirmTwoFactor(
        action.pin,
        action.onError,
        action.isLoginPage,
      )
      break
    case Actions.DISABLE_TWO_FACTOR:
      controller.disableTwoFactor()
      break
    case Actions.OAUTH:
      controller.oauth(action.oauthType, action.data)
      break
    case Actions.TWO_FACTOR_LOGIN:
      controller.twoFactorLogin(action.pin, action.onError)
      break
    case Actions.UPDATE_SUBSCRIPTION:
      controller.updateSubscription(action.hostedPageId)
      break
    default:
  }
})

controller.store = store
export default controller.store
