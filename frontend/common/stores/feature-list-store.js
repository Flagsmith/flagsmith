const BaseStore = require('./base/_store');
const OrganisationStore = require('./organisation-store');
const data = require('../data/base/_data');

let createdFirstFeature = false;

const controller = {

    getFeatures: (projectId, environmentId, force) => {
        if (!store.model || store.envId != environmentId || force) { // todo: change logic a bit
            store.loading();
            store.envId = environmentId;

            // todo: cache project flags
            return Promise.all([
                data.get(`${Project.api}projects/${projectId}/features/?page_size=999`),
                data.get(`${Project.api}environments/${environmentId}/featurestates/?page_size=999`),
            ]).then(([features, environmentFeatures]) => {
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
    createFlag(projectId, environmentId, flag, segmentOverrides) {
        store.saving();
        API.trackEvent(Constants.events.CREATE_FEATURE);
        if ((!createdFirstFeature && !flagsmith.getTrait('first_feature')) && AccountStore.model.organisations.length === 1 && OrganisationStore.model.projects.length === 1 && (!store.model.features || !store.model.features.length)) {
            createdFirstFeature = true;
            flagsmith.setTrait('first_feature', 'true');
            API.trackEvent(Constants.events.CREATE_FIRST_FEATURE);
        }
        data.post(`${Project.api}projects/${projectId}/features/`, Object.assign({}, flag, { project: projectId, type: flag.multivariate_options && flag.multivariate_options.length ? 'MULTIVARIATE' : 'STANDARD',
        }))
            .then(res => Promise.all([
                data.get(`${Project.api}projects/${projectId}/features/`),
                data.get(`${Project.api}environments/${environmentId}/featurestates/`),
            ]).then(([features, environmentFeatures]) => {
                store.model = {
                    features: features.results,
                    keyedEnvironmentFeatures: environmentFeatures && _.keyBy(environmentFeatures.results, 'feature'),
                };
                store.model.lastSaved = new Date().valueOf();
                store.saved();
            }))
            .catch(e => API.ajaxHandler(store, e));
    },
    parseFlag(flag) {
        return {
            ...flag,
            feature_segments: flag.feature_segments && flag.feature_segments.map(fs => ({
                ...fs,
                segment: fs.segment.id,
            })),
        };
    },
    editFlag(projectId, flag, onComplete) {
        data.put(`${Project.api}projects/${projectId}/features/${flag.id}/`, {
            ...flag,
            type: flag.multivariate_options && flag.multivariate_options.length ? 'MULTIVARIATE' : 'STANDARD',
            project: projectId,
        })
            .then((res) => {
                if (onComplete) {
                    onComplete(res);
                }
                const index = _.findIndex(store.model.features, { id: flag.id });
                store.model.features[index] = controller.parseFlag(flag);
                store.model.lastSaved = new Date().valueOf();
                store.changed();
            })
            .catch(e => {
                if (onComplete) {
                    onComplete({
                        ...flag,
                        type: flag.multivariate_options && flag.multivariate_options.length ? 'MULTIVARIATE' : 'STANDARD',
                        project: projectId,
                    })
                } else {
                    API.ajaxHandler(store, e)
                }
            });
    },
    getInfluxDate(projectId, environmentId, flag, period) {
        data.get(`${Project.api}projects/${projectId}/features/${flag}/influx-data/?period=${period}&environment_id=${environmentId}`)
            .then((result) => {
                store.model.influxData = result;
                store.changed();
            }).catch(e => API.ajaxHandler(store, e));
    },
    toggleFlag: (index, environments, comment, environmentFlags) => {
        const flag = store.model.features[index];
        store.saving();

        API.trackEvent(Constants.events.TOGGLE_FEATURE);
        return Promise.all(environments.map((e) => {
            if (store.hasFlagInEnvironment(flag.id, environmentFlags)) {
                const environmentFlag = (environmentFlags || store.model.keyedEnvironmentFeatures)[flag.id];
                return data.put(`${Project.api}environments/${e.api_key}/featurestates/${environmentFlag.id}/`, Object.assign({}, environmentFlag, { enabled: !environmentFlag.enabled }));
            }
            return data.post(`${Project.api}environments/${e.api_key}/featurestates/`, Object.assign({}, {
                feature: flag.id,
                enabled: true,
                comment,
            }));
        }))
            .then((res) => {
                if (!environmentFlags) {
                    store.model.keyedEnvironmentFeatures[flag.id] = res[0];
                }
                store.model.lastSaved = new Date().valueOf();
                store.saved();
            });
    },
    editFeatureState: (projectId, environmentId, flag, projectFlag, environmentFlag, segmentOverrides, mode) => {
        let prom;
        store.saving();
        API.trackEvent(Constants.events.EDIT_FEATURE);
        if (mode !== "VALUE") {
            prom = Promise.resolve()
        } else {
            if (environmentFlag) {
                prom = data.get(`${Project.api}environments/${environmentId}/featurestates/${environmentFlag.id}/`)
                    .then((environmentFeatureStates) => {
                        const multivariate_feature_state_values = environmentFeatureStates.multivariate_feature_state_values && environmentFeatureStates.multivariate_feature_state_values.map((v) => {
                            const matching = flag.multivariate_options.find(m => m.id === v.multivariate_feature_option);
                            if (!matching) { // multivariate is new, meaning the value is already correct from the default allocation
                                return v;
                            }
                            // multivariate is existing, override the existing with the new value
                            return { ...v, percentage_allocation: matching.default_percentage_allocation };
                        });
                        environmentFlag.multivariate_feature_state_values = multivariate_feature_state_values;
                        return data.put(`${Project.api}environments/${environmentId}/featurestates/${environmentFlag.id}/`, Object.assign({}, environmentFlag, {
                            feature_state_value: flag.initial_value,
                            hide_from_client: flag.hide_from_client,
                            enabled: flag.default_enabled,
                        }));
                    });
            } else {
                prom = data.post(`${Project.api}environments/${environmentId}/featurestates/`, Object.assign({}, flag, {
                    enabled: false,
                    environment: environmentId,
                    feature: projectFlag,
                }));
            }

        }

        const segmentOverridesRequest = mode === "SEGMENT" && segmentOverrides
            ? data.post(`${Project.api}features/feature-segments/update-priorities/`, segmentOverrides.map((override, index) => ({
                id: override.id,
                priority: index,
            }))).then(() => Promise.all(segmentOverrides.map(override => data.put(`${Project.api}features/featurestates/${override.feature_segment_value.id}/`, {
                ...override.feature_segment_value,
                multivariate_feature_state_values: override.multivariate_options && override.multivariate_options.map((o) => {
                    if (o.multivariate_feature_option) return o;
                    return {
                        multivariate_feature_option: environmentFlag.multivariate_feature_state_values[o.multivariate_feature_option_index].multivariate_feature_option,
                        percentage_allocation: o.percentage_allocation,
                    };
                }),
                feature_state_value: Utils.valueToFeatureState(override.value),
                enabled: override.enabled,
            })))) : Promise.resolve();


        Promise.all([prom, segmentOverridesRequest]).then(([res, segmentRes]) => {
            store.model.keyedEnvironmentFeatures[projectFlag.id] = res;
            if (segmentRes) {
                const feature = _.find(store.model.features, f => f.id === projectFlag.id);
                if (feature) feature.feature_segments = _.map(segmentRes.feature_segments, segment => ({ ...segment, segment: segment.segment.id }));
            }
            store.model.lastSaved = new Date().valueOf();
            store.saved();
        });
    },
    editFeatureStateChangeRequest: (projectId, environmentId, flag, projectFlag, environmentFlag, segmentOverrides, changeRequest) => {
        let prom;
        store.saving();
        API.trackEvent(Constants.events.EDIT_FEATURE);

        data.get(`${Project.api}environments/${environmentId}/featurestates/${environmentFlag.id}/`)
            .then((environmentFeatureStates) => {
                const multivariate_feature_state_values = environmentFeatureStates.multivariate_feature_state_values && environmentFeatureStates.multivariate_feature_state_values.map((v) => {
                    const matching = flag.multivariate_options.find(m => m.id === v.multivariate_feature_option);
                    if (!matching) { // multivariate is new, meaning the value is already correct from the default allocation
                        return v;
                    }
                    // multivariate is existing, override the existing with the new value
                    return { ...v, percentage_allocation: matching.default_percentage_allocation };
                });
                debugger
                const req = {
                    featurestates: [{
                        feature: projectFlag,
                        enabled: flag.default_enabled,
                        feature_state_value: Utils.valueToFeatureState(flag.initial_value),
                        live_from: new Date().toISOString(),
                        multivariate_feature_state_values,
                    }],
                    ...changeRequest,
                }
                data.post(`${Project.api}environments/${environmentId}/create-change-request`, req)
            })


        Promise.all([prom, segmentOverridesRequest]).then(([res, segmentRes]) => {
            store.model.keyedEnvironmentFeatures[projectFlag.id] = res;
            if (segmentRes) {
                const feature = _.find(store.model.features, f => f.id === projectFlag.id);
                if (feature) feature.feature_segments = _.map(segmentRes.feature_segments, segment => ({ ...segment, segment: segment.segment.id }));
            }
            store.model.lastSaved = new Date().valueOf();
            store.saved();
        });
    },
    removeFlag: (projectId, flag) => {
        store.saving();
        API.trackEvent(Constants.events.REMOVE_FEATURE);
        return data.delete(`${Project.api}projects/${projectId}/features/${flag.id}/`)
            .then(() => {
                store.model.features = _.filter(store.model.features, f => f.id != flag.id);
                store.model.lastSaved = new Date().valueOf();
                store.saved();
            });
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
