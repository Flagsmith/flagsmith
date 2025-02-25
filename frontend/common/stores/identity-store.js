import Constants from 'common/constants'
import Utils from 'common/utils/utils'

const Dispatcher = require('../dispatcher/dispatcher')
const BaseStore = require('./base/_store')
const data = require('../data/base/_data')

const controller = {
  changeUserFlag({
    environmentId,
    identity,
    identityFlag,
    onSuccess,
    payload,
  }) {
    store.saving()
    API.trackEvent(Constants.events.TOGGLE_USER_FEATURE)

    const prom = data.put(
      `${
        Project.api
      }environments/${environmentId}/${Utils.getIdentitiesEndpoint()}/${identity}/${Utils.getFeatureStatesEndpoint()}/${identityFlag}/`,
      Object.assign({}, payload),
    )
    prom.then(() => {
      if (onSuccess) onSuccess()
      store.saved()
    })
  },

  editUserFlag({ environmentId, identity, identityFlag, projectFlag }) {
    store.saving()
    API.trackEvent(Constants.events.EDIT_USER_FEATURE)
    const prom =
      identityFlag.identity || identityFlag.identity_uuid
        ? data.put(
            `${
              Project.api
            }environments/${environmentId}/${Utils.getIdentitiesEndpoint()}/${identity}/${Utils.getFeatureStatesEndpoint()}/${
              identityFlag.id || identityFlag.featurestate_uuid
            }/`,
            Object.assign(
              {},
              {
                enabled: identityFlag.enabled,
                feature: projectFlag.id,
                feature_state_value: Utils.getTypedValue(
                  identityFlag.feature_state_value,
                  undefined,
                  true,
                ),
                id: identityFlag.id || identityFlag.featurestate_uuid,
                multivariate_feature_state_values:
                  identityFlag.multivariate_options,
              },
            ),
          )
        : data.post(
            `${
              Project.api
            }environments/${environmentId}/${Utils.getIdentitiesEndpoint()}/${identity}/${Utils.getFeatureStatesEndpoint()}/`,
            {
              enabled: identityFlag.enabled,
              feature: projectFlag.id,
              feature_state_value: Utils.getTypedValue(
                identityFlag.feature_state_value,
                undefined,
                true,
              ),
              multivariate_feature_state_values:
                identityFlag.multivariate_options,
            },
          )

    prom.then(() =>
      controller.getIdentity(environmentId, identity).then(() => store.saved()),
    )
  },
  getIdentity: (envId, id) => {
    store.loading()
    return data
      .get(
        `${
          Project.api
        }environments/${envId}/${Utils.getIdentitiesEndpoint()}/${id}/`,
      )
      .then((identity) =>
        Promise.all([
          Promise.resolve(identity),
          data.get(
            `${
              Project.api
            }environments/${envId}/${Utils.getIdentitiesEndpoint()}/${id}/${Utils.getFeatureStatesEndpoint()}/`,
          ),
        ]),
      )
      .then(([identity, flags]) => {
        const features = (flags && flags.results) || flags

        store.model = store.model || {}
        store.model.features = features && _.keyBy(features, (f) => f.feature)
        store.model.identity = identity
        store.loaded()
      })
      .catch((e) => API.ajaxHandler(store, e))
  },
  removeUserFlag(identity, identityFlag, environmentId, cb) {
    store.saving()
    API.trackEvent(Constants.events.REMOVE_USER_FEATURE)
    data
      .delete(
        `${
          Project.api
        }environments/${environmentId}/${Utils.getIdentitiesEndpoint()}/${identity}/${Utils.getFeatureStatesEndpoint()}/${
          identityFlag.id || identityFlag.featurestate_uuid
        }/`,
      )
      .then(() =>
        controller.getIdentity(environmentId, identity).then(() => {
          store.saved()
          if (cb) {
            cb()
          }
        }),
      )
  },
  toggleUserFlag({
    environmentFlag,
    environmentId,
    identity,
    identityFlag,
    projectFlag,
  }) {
    store.saving()
    API.trackEvent(Constants.events.TOGGLE_USER_FEATURE)
    const prom =
      identityFlag.identity || identityFlag.identity_uuid
        ? data.put(
            `${
              Project.api
            }environments/${environmentId}/${Utils.getIdentitiesEndpoint()}/${identity}/${Utils.getFeatureStatesEndpoint()}/${
              identityFlag.id || identityFlag.featurestate_uuid
            }/`,
            Object.assign(
              {},
              {
                enabled: !identityFlag.enabled,
                feature: projectFlag.id,
                feature_state_value: identityFlag
                  ? identityFlag.feature_state_value
                  : environmentFlag && environmentFlag.feature_state_value,
                id: identityFlag.id || identityFlag.featurestate_uuid,
              },
            ),
          )
        : data.post(
            `${
              Project.api
            }environments/${environmentId}/${Utils.getIdentitiesEndpoint()}/${identity}/${Utils.getFeatureStatesEndpoint()}/`,
            {
              enabled: !environmentFlag || !environmentFlag.enabled,
              feature: projectFlag.id,
              feature_state_value: environmentFlag
                ? environmentFlag.feature_state_value
                : undefined,
            },
          )

    prom.then((res) => {
      store.model.features[res.feature] = res
      store.saved()
    })
  },
}

const store = Object.assign({}, BaseStore, {
  getIdentityFlags() {
    return store.model && store.model.features
  },
  getIdentityForEditing() {
    return store.model && _.cloneDeep(store.model) // immutable
  },
  id: 'identity',
})

store.dispatcherIndex = Dispatcher.register(store, (payload) => {
  const action = payload.action // this is our action from handleViewAction
  const {
    cb,
    environmentFlag,
    environmentId,
    identity,
    identityFlag,
    projectFlag,
    trait,
  } = action
  switch (action.actionType) {
    case Actions.GET_IDENTITY:
      controller.getIdentity(action.envId, action.id)
      break
    case Actions.TOGGLE_USER_FLAG:
      controller.toggleUserFlag({
        environmentFlag,
        environmentId,
        identity,
        identityFlag,
        projectFlag,
      })
      break
    case Actions.EDIT_USER_FLAG:
      controller.editUserFlag({
        environmentFlag,
        environmentId,
        identity,
        identityFlag,
        projectFlag,
      })
      break
    case Actions.REMOVE_USER_FLAG:
      controller.removeUserFlag(identity, identityFlag, environmentId, cb)
      break
    case Actions.CHANGE_USER_FLAG:
      controller.changeUserFlag(action.identity)
      break
    default:
  }
})
controller.store = store
module.exports = controller.store
