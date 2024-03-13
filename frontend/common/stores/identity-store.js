import Constants from 'common/constants'

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
  deleteIdentityTrait(envId, identity, id) {
    store.saving()
    if (Utils.getShouldUpdateTraitOnDelete()) {
      controller.editTrait({
        environmentId: envId,
        identity,
        trait: {
          trait_key: id,
          trait_value: null,
        },
      })
      return
    }
    data
      .delete(
        `${
          Project.api
        }environments/${envId}/${Utils.getIdentitiesEndpoint()}/${identity}/traits/${id}/`,
      )
      .then(() => {
        const index = _.findIndex(
          store.model.traits,
          (trait) => trait.id === id,
        )
        if (index !== -1) {
          store.model.traits.splice(index, 1)
        }
        store.saved()
      })
      .catch((e) => API.ajaxHandler(store, e))
  },
  editTrait({ environmentId, identity, trait }) {
    const { id, trait_key, trait_value } = trait
    store.saving()
    data[Utils.getTraitEndpointMethod(id)](
      Utils.getUpdateTraitEndpoint(environmentId, identity, id),
      {
        identity: Utils.getShouldSendIdentityToTraits()
          ? { identifier: store.model && store.model.identity.identifier }
          : undefined,
        trait_key,
        ...(Utils.getIsEdge()
          ? { trait_value }
          : Utils.valueToTrait(trait_value)),
      },
    )
      .then(() =>
        controller
          .getIdentity(environmentId, identity)
          .then(() => store.saved()),
      )
      .catch((e) => API.ajaxHandler(store, e))
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
                feature_state_value: identityFlag.feature_state_value,
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
              feature_state_value: identityFlag.feature_state_value,
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
          data.get(Utils.getTraitEndpoint(envId, id)),
          Promise.resolve(identity),
          data.get(
            `${
              Project.api
            }environments/${envId}/${Utils.getIdentitiesEndpoint()}/${id}/${Utils.getFeatureStatesEndpoint()}/`,
          ),
        ]),
      )
      .then(([res, identity, flags]) => {
        const features = (flags && flags.results) || flags
        const traits = Utils.getIsEdge()
          ? res
          : res &&
            res.results &&
            res.results.map((v) => ({
              id: v.id,
              trait_key: v.trait_key,
              trait_value: Utils.featureStateToValue(v),
            }))
        store.model = store.model || {}
        store.model.features = features && _.keyBy(features, (f) => f.feature)
        store.model.traits = traits
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
  getTraits() {
    return store.model && store.model.traits
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
    case Actions.EDIT_TRAIT:
      controller.editTrait({ environmentId, identity, trait })
      break
    case Actions.REMOVE_USER_FLAG:
      controller.removeUserFlag(identity, identityFlag, environmentId, cb)
      break
    case Actions.DELETE_IDENTITY_TRAIT:
      controller.deleteIdentityTrait(action.envId, action.identity, action.id)
      break
    case Actions.CHANGE_USER_FLAG:
      controller.changeUserFlag(action.identity)
      break
    default:
  }
})
controller.store = store
module.exports = controller.store
