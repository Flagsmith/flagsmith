const BaseStore = require('./base/_store');
const OrganisationStore = require('./organisation-store');
const data = require('../data/base/_data');

let createdFirstFeature = false;

const controller = {

    getFeatures: (projectId, environmentId, force) => {
        if (!store.model || store.envId != environmentId || force) { // todo: change logic a bit
            store.loading();
            store.envId = environmentId;
            return data.get(`${Project.api}projects/${projectId}/features/?page_size=999`).then(([features]) => {
                if (features.results.length) {
                    createdFirstFeature = true;
                }
                store.model = {
                    features: features.results.map((controller.parseFlag)),
                    keyedEnvironmentFeatures: environmentFeatures.results && _.keyBy(environmentFeatures.results, 'feature'),
                };
                store.loaded();
            }).catch((e) => {
                document.location.href = '/404?entity=environment';
                API.ajaxHandler(store, e);
            });
        }
    },


};


const store = Object.assign({}, BaseStore, {
    id: 'features',
    getEnvironmentFlags() {
        return store.model && store.model.keyedEnvironmentFeatures;
    },
    getProjectFlags() {
        return store.model && store.model.features;
    },
    hasFlagInEnvironment(id, environmentFlags) {
        const flags = environmentFlags || (store.model && store.model.keyedEnvironmentFeatures);

        return flags && flags.hasOwnProperty(id);
    },
    getLastSaved() {
        return store.model && store.model.lastSaved;
    },
    getFlagInfluxData() {
        return store.model && store.model.influxData;
    },
});


store.dispatcherIndex = Dispatcher.register(store, (payload) => {
    const action = payload.action; // this is our action from handleViewAction

    switch (action.actionType) {
        case Actions.GET_FLAGS:
            controller.getFeatures(action.projectId, action.environmentId, action.force);
            break;
        case Actions.TOGGLE_FLAG:
            controller.toggleFlag(action.index, action.environments, action.comment, action.environmentFlags);
            break;
        case Actions.GET_FLAG_INFLUX_DATA:
            controller.getInfluxDate(action.projectId, action.environmentId, action.flag, action.period);
            break;
        case Actions.CREATE_FLAG:
            controller.createFlag(action.projectId, action.environmentId, action.flag, action.segmentOverrides);
            break;
        case Actions.EDIT_ENVIRONMENT_FLAG:
            controller.editFeatureState(action.projectId, action.environmentId, action.flag, action.projectFlag, action.environmentFlag, action.segmentOverrides, action.mode);
            break;
        case Actions.EDIT_ENVIRONMENT_FLAG_CHANGE_REQUEST:
            controller.editFeatureStateChangeRequest(action.projectId, action.environmentId, action.flag, action.projectFlag, action.environmentFlag, action.segmentOverrides, action.changeRequest);
            break;
        case Actions.EDIT_FLAG:
            controller.editFlag(action.projectId, action.flag, action.onComplete);
            break;
        case Actions.REMOVE_FLAG:
            controller.removeFlag(action.projectId, action.flag);
            break;
        default:
    }
});
controller.store = store;
module.exports = controller.store;
