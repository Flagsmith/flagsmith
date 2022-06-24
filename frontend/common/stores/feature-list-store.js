const BaseStore = require('./base/_store');
const OrganisationStore = require('./organisation-store');
const data = require('../data/base/_data');

let createdFirstFeature = false;
const PAGE_SIZE = 10;
const controller = {

    getFeatures: (projectId, environmentId, force, page,filter) => {
        if (!store.model || store.envId != environmentId || force) { // todo: change logic a bit
            store.loading();
            store.envId = environmentId;
            store.projectId = projectId;
            store.environmentId = environmentId
            store.page = page
            store.filter=filter
            let filterUrl = ''
            const { feature } = Utils.fromParam();
            if (Object.keys(store.filter).length) {
                filterUrl = '&'+Utils.toParam(store.filter)
            }

            let featuresEndpoint = `${Project.api}projects/${projectId}/features/?page=${page || 1}&page_size=${PAGE_SIZE}${filterUrl}`;
            if (store.search) {
                featuresEndpoint += `&search=${store.search}`;
            }
            if (store.sort) {
                featuresEndpoint += `&sort_field=${store.sort.sortBy}&sort_direction=${store.sort.sortOrder.toUpperCase()}`;
            }
            return Promise.all([
                data.get(featuresEndpoint),
                data.get(`${Project.api}environments/${environmentId}/featurestates/?page_size=${PAGE_SIZE}`),
                feature ? data.get(`${Project.api}projects/${projectId}/features/${feature}/`) : Promise.resolve(),
            ]).then(([features, environmentFeatures, feature]) => {
                store.paging.next = features.next;
                store.paging.pageSize = PAGE_SIZE;
                store.paging.count = features.count;
                store.paging.previous = features.previous;
                store.paging.currentPage = featuresEndpoint.indexOf('?page=') !== -1 ? parseInt(featuresEndpoint.substr(featuresEndpoint.indexOf('?page=') + 6)) : 1;


                if (feature) {
                    const index = features.results.findIndex(v => v.id === feature.id);
                    if (index === -1) {
                        features.results.push({ ...feature, ignore: true });
                    }
                }
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
        data.post(`${Project.api}projects/${projectId}/features/`, Object.assign({}, flag, { multivariate_options: undefined, project: projectId, type: flag.multivariate_options && flag.multivariate_options.length ? 'MULTIVARIATE' : 'STANDARD',
        }))
            .then(res => Promise.all((flag.multivariate_options || []).map(v => data.post(`${Project.api}projects/${projectId}/features/${flag.id}/mv-options/`, {
                ...v,
                feature: res.id,
            }).then(() => res))).then(() => data.get(`${Project.api}projects/${projectId}/features/${res.id}`)))
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
        const originalFlag = store.model.features.find(v => v.id === flag.id);

        Promise.all((flag.multivariate_options || []).map((v, i) => {
            const originalMV = v.id ? originalFlag.multivariate_options.find(m => m.id === v.id) : null;
            return (originalMV ? data.put(`${Project.api}projects/${projectId}/features/${flag.id}/mv-options/${originalMV.id}/`, {
                ...v,
                feature: flag.id,
                default_percentage_allocation: 0,
            }) : data.post(`${Project.api}projects/${projectId}/features/${flag.id}/mv-options/`, {
                ...v,
                feature: flag.id,
                default_percentage_allocation: 0,
            })).then((res) => {
                flag.multivariate_options[i] = res;
                return {
                    ...v,
                    id: res.id,
                };
            });
        })).then(() => {
            const deletedMv = originalFlag.multivariate_options.filter(v => !flag.multivariate_options.find(x => v.id === x.id));
            return Promise.all(deletedMv.map(v => data.delete(`${Project.api}projects/${projectId}/features/${flag.id}/mv-options/${v.id}/`)));
        })
            .then(() => data.put(`${Project.api}projects/${projectId}/features/${flag.id}/`, {
                ...flag,
                multivariate_options: undefined,
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
                .catch((e) => {
                    if (onComplete) {
                        onComplete({
                            ...flag,
                            type: flag.multivariate_options && flag.multivariate_options.length ? 'MULTIVARIATE' : 'STANDARD',
                            project: projectId,
                        });
                    } else {
                        API.ajaxHandler(store, e);
                    }
                }));
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
        if (mode !== 'VALUE') {
            prom = Promise.resolve();
        } else if (environmentFlag) {
            prom = data.get(`${Project.api}environments/${environmentId}/featurestates/${environmentFlag.id}/`)
                .then((environmentFeatureStates) => {
                    const multivariate_feature_state_values = environmentFeatureStates.multivariate_feature_state_values && environmentFeatureStates.multivariate_feature_state_values.map((v, i) => {
                        const matching = environmentFlag.multivariate_feature_state_values[i];
                        return {
                            ...v,
                            percentage_allocation: matching.default_percentage_allocation,
                        };
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

        const segmentOverridesRequest = mode === 'SEGMENT' && segmentOverrides
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
    editFeatureStateChangeRequest: (projectId, environmentId, flag, projectFlag, environmentFlag, segmentOverrides, changeRequest, commit) => {
        store.saving();
        API.trackEvent(Constants.events.EDIT_FEATURE);

        const prom = data.get(`${Project.api}environments/${environmentId}/featurestates/${environmentFlag.id}/`)
            .then((environmentFeatureStates) => {
                const multivariate_feature_state_values = environmentFeatureStates.multivariate_feature_state_values && environmentFeatureStates.multivariate_feature_state_values.map((v) => {
                    const matching = flag.multivariate_options.find(m => m.id === v.multivariate_feature_option);
                    if (!matching) { // multivariate is new, meaning the value is already correct from the default allocation
                        return v;
                    }
                    // multivariate is existing, override the existing with the new value
                    return { ...v, percentage_allocation: matching.default_percentage_allocation };
                });
                const { featureStateId, multivariate_options, ...changeRequestData } = changeRequest;
                const req = {
                    feature_states: [{
                        id: featureStateId,
                        feature: projectFlag.id,
                        enabled: flag.default_enabled,
                        feature_state_value: Utils.valueToFeatureState(flag.initial_value),
                        live_from: changeRequest.live_from || new Date().toISOString(),
                    }],
                    ...changeRequestData,
                };
                const reqType = req.id ? 'put' : 'post';
                const url = req.id ? `${Project.api}features/workflows/change-requests/${req.id}/` : `${Project.api}environments/${environmentId}/create-change-request/`;
                return data[reqType](url, req).then((v) => {
                    let prom = Promise.resolve();
                    if (multivariate_options) {
                        v.feature_states[0].multivariate_feature_state_values = v.feature_states[0].multivariate_feature_state_values.map(
                            (v) => {
                                const matching = multivariate_options.find(m => (v.multivariate_feature_option || v.id) === (m.multivariate_feature_option || m.id));
                                return ({ ...v,
                                    percentage_allocation: matching
                                        ? typeof matching.percentage_allocation === 'number' ? matching.percentage_allocation
                                            : matching.default_percentage_allocation : v.percentage_allocation,
                                });
                            },
                        );
                    }


                    prom = data.put(`${Project.api}features/workflows/change-requests/${v.id}/`, {
                        ...v,
                    }).then((v) => {
                        if (commit) {
                            AppActions.actionChangeRequest(v.id, 'commit', () => {
                                AppActions.refreshFeatures(projectId, environmentId);
                            });
                        } else {
                            AppActions.getChangeRequest(v.id, projectId, environmentId);
                        }
                    });
                    prom.then(() => {
                        AppActions.getChangeRequests(environmentId, {});
                        AppActions.getChangeRequests(environmentId, { committed: true });
                        AppActions.getChangeRequests(environmentId, { live_from_after: new Date().toISOString() });

                        if (featureStateId) {
                            AppActions.getChangeRequest(changeRequestData.id, projectId, environmentId);
                        }
                    });
                });
            });


        Promise.all([prom]).then(([res, segmentRes]) => {
            store.saved();
            if (typeof closeModal !== 'undefined') {
                closeModal();
            }
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
    searchFeatures: _.throttle((search, environmentId, projectId, filter) => {
        store.search = search;
        controller.getFeatures(projectId, environmentId, true, 0, filter);
    }, 1000),
};


const store = Object.assign({}, BaseStore, {
    id: 'features',
    paging: {},
    sort: { label: 'Name', sortBy: 'name', sortOrder: 'asc', default: true },
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
        case Actions.SEARCH_FLAGS:
            controller.searchFeatures(action.search, action.environmentId, action.projectId, action.filter);
            break;
        case Actions.GET_FLAGS:
            store.search = action.search || '';
            if (action.sort) {
                store.sort = action.sort;
            }
            controller.getFeatures(action.projectId, action.environmentId, action.force, action.page, action.filter);
            break;
        case Actions.REFRESH_FEATURES:
            if (action.projectId === store.projectId && action.environmentId === store.environmentId) {
                controller.getFeatures(store.projectId, store.environmentId, true, store.page, store.filter);
            }
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
            controller.editFeatureStateChangeRequest(action.projectId, action.environmentId, action.flag, action.projectFlag, action.environmentFlag, action.segmentOverrides, action.changeRequest, action.commit);
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
