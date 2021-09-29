const BaseStore = require('./base/_store');
const data = require('../data/base/_data');


const controller = {

    getIdentity: (envId, id) => {
        store.loading();
        return data.get(`${Project.api}environments/${envId}/identities/${id}/`)
            .then(identity => Promise.all([
                data.get(`${Project.api}identities/?identifier=${encodeURIComponent(identity.identifier)}`, null, { 'x-environment-key': envId }),
                Promise.resolve(identity),
                data.get(`${Project.api}environments/${envId}/identities/${id}/featurestates/`),
            ]))
            .then(([res, identity, flags]) => {
                const features = flags && flags.results;
                const traits = res.traits;
                store.model = store.model || {};
                store.model.features = features && _.keyBy(features, f => f.feature);
                store.model.traits = traits;
                store.model.identity = identity;
                store.loaded();
            })
            .catch(e => API.ajaxHandler(store, e));
    },
    toggleUserFlag({ identity, projectFlag, environmentFlag, identityFlag, environmentId }) {
        store.saving();
        API.trackEvent(Constants.events.TOGGLE_USER_FEATURE);
        const prom = identityFlag.identity
            ? data.put(`${Project.api}environments/${environmentId}/identities/${identity}/featurestates/${identityFlag.id}/`, Object.assign({}, {
                id: identityFlag.id,
                enabled: !identityFlag.enabled,
                value: identityFlag.value,
            }))
            : data.post(`${Project.api}environments/${environmentId}/identities/${identity}/featurestates/`, {
                feature: projectFlag.id,
                enabled: !environmentFlag.enabled,
                value: environmentFlag.value,
            });

        prom.then((res) => {
            store.model.features[res.feature] = res;
            store.saved();
        });
    },
    changeUserFlag({ identity, identityFlag, environmentId, payload, onSuccess }) {
        store.saving();
        API.trackEvent(Constants.events.TOGGLE_USER_FEATURE);

        const prom = data.put(`${Project.api}environments/${environmentId}/identities/${identity}/featurestates/${identityFlag}/`, Object.assign({}, payload));
        prom.then((res) => {
            if (onSuccess) onSuccess();
            store.saved();
        });
    },
    editTrait({ identity, environmentId, trait: { trait_key, trait_value } }) {
        store.saving();
        data.post(`${Project.api}traits/`, { identity: { identifier: store.model && store.model.identity.identifier }, trait_key, trait_value }, { 'x-environment-key': environmentId })
            .then(() => controller.getIdentity(environmentId, identity)
                .then(() => store.saved()))
            .catch(e => API.ajaxHandler(store, e));
    },
    editUserFlag({ identity, projectFlag, environmentFlag, identityFlag, environmentId }) {
        store.saving();
        API.trackEvent(Constants.events.EDIT_USER_FEATURE);
        const prom = identityFlag.identity
            ? data.put(`${Project.api}environments/${environmentId}/identities/${identity}/featurestates/${identityFlag.id}/`, Object.assign({}, {
                id: identityFlag.id,
                enabled: identityFlag.enabled,
                multivariate_feature_state_values:identityFlag.multivariate_options,
                feature_state_value: identityFlag.feature_state_value,
            }))
            : data.post(`${Project.api}environments/${environmentId}/identities/${identity}/featurestates/`, {
                feature: projectFlag.id,
                enabled: identityFlag.enabled,
                multivariate_feature_state_values:identityFlag.multivariate_options,
                feature_state_value: identityFlag.feature_state_value,
            });

        prom.then(res => controller.getIdentity(environmentId, identity)
            .then(() => store.saved()));
    },
    removeUserFlag(identity, identityFlag, environmentId) {
        store.saving();
        API.trackEvent(Constants.events.REMOVE_USER_FEATURE);
        data.delete(`${Project.api}environments/${environmentId}/identities/${identity}/featurestates/${identityFlag.id}/`)
            .then(() => controller.getIdentity(environmentId, identity)
                .then(() => store.saved()));
    },
    deleteIdentityTrait(envId, identity, id) {
        store.saving();
        data.delete(`${Project.api}environments/${envId}/identities/${identity}/traits/${id}/`)
            .then(() => {
                const index = _.findIndex(store.model.traits, trait => trait.id === id);
                if (index !== -1) {
                    store.model.traits.splice(index, 1);
                }
                store.saved();
            })
            .catch(e => API.ajaxHandler(store, e));
    },
};


var store = Object.assign({}, BaseStore, {
    id: 'identity',
    getIdentityForEditing(id) {
        return store.model && _.cloneDeep(store.model); // immutable
    },
    getIdentityFlags() {
        return store.model && store.model.features;
    },
    getTraits() {
        return store.model && store.model.traits;
    },
});


store.dispatcherIndex = Dispatcher.register(store, (payload) => {
    const action = payload.action; // this is our action from	handleViewAction
    const {
        identity, projectFlag, environmentFlag, identityFlag, environmentId, trait,
    } = action;
    switch (action.actionType) {
        case Actions.GET_IDENTITY:
            controller.getIdentity(action.envId, action.id);
            break;
        case Actions.SAVE_IDENTITY:
            controller.saveIdentity(action.id, action.identity);
            break;
        case Actions.TOGGLE_USER_FLAG:
            controller.toggleUserFlag({ identity, projectFlag, environmentFlag, identityFlag, environmentId });
            break;
        case Actions.EDIT_USER_FLAG:
            controller.editUserFlag({ identity, projectFlag, environmentFlag, identityFlag, environmentId });
            break;
        case Actions.EDIT_TRAIT:
            controller.editTrait({ identity, environmentId, trait });
            break;
        case Actions.REMOVE_USER_FLAG:
            controller.removeUserFlag(identity, identityFlag, environmentId);
            break;
        case Actions.DELETE_IDENTITY_TRAIT:
            controller.deleteIdentityTrait(action.envId, action.identity, action.id);
            break;
        case Actions.CHANGE_USER_FLAG:
            controller.changeUserFlag(action.identity);
            break;
        default:
    }
});
controller.store = store;
module.exports = controller.store;
