const BaseStore = require('./base/_store');
const OrganisationStore = require('./organisation-store');
const data = require('../data/base/_data');


const controller = {

    getSegments: (projectId, environmentId) => {
        if (!store.model || store.envId != environmentId) { // todo: change logic a bit
            store.loading();
            store.envId = environmentId;
            data.get(`${Project.api}projects/${projectId}/segments/`)
                .then((res) => {
                    store.model = res.results && _.sortBy(res.results, 'name');
                    store.loaded();
                });
        }
    },
    createSegment(projectId, _data) {
        store.saving();
        if (AccountStore.model.organisations.length === 1 && OrganisationStore.model.projects.length === 1 && (!store.model || !store.model.length)) {
            API.trackEvent(Constants.events.CREATE_FIRST_SEGMENT);
        }
        API.trackEvent(Constants.events.CREATE_SEGMENT);
        data.post(`${Project.api}projects/${projectId}/segments/`, {
            ..._data,
            project: parseInt(projectId),
        })
            .then((res) => {
                data.get(`${Project.api}projects/${projectId}/segments/`)
                    .then((res) => {
                        store.model = res.results && _.sortBy(res.results, 'name');
                        store.loaded();
                        store.saved();
                    });
            }).catch(e => API.ajaxHandler(store, e));
    },
    editSegment(projectId, _data) {
        data.put(`${Project.api}projects/${projectId}/segments/${_data.id}/`, {
            ..._data,
            project: parseInt(projectId),
        })
            .then((res) => {
                data.get(`${Project.api}projects/${projectId}/segments/`)
                    .then((res) => {
                        store.model = res.results && _.sortBy(res.results, 'name');
                        store.loaded();
                        store.saved();
                    });
            });
    },
    removeSegment: (projectId, id) => {
        store.saving();
        API.trackEvent(Constants.events.REMOVE_FEATURE);
        return data.delete(`${Project.api}projects/${projectId}/segments/${id}/`)
            .then(() => {
                data.get(`${Project.api}projects/${projectId}/segments/`)
                    .then((res) => {
                        store.model = res.results && _.sortBy(res.results, 'name');
                        store.loaded();
                        store.saved();
                    });
            });
    },

};


var store = Object.assign({}, BaseStore, {
    id: 'segments',
    getSegments() {
        return store.model;
    },
});


store.dispatcherIndex = Dispatcher.register(store, (payload) => {
    const action = payload.action; // this is our action from handleViewAction

    switch (action.actionType) {
        case Actions.GET_SEGMENTS:
            controller.getSegments(action.projectId, action.environmentId);
            break;
        case Actions.CREATE_SEGMENT:
            controller.createSegment(action.projectId, action.data);
            break;
        case Actions.EDIT_SEGMENT:
            controller.editSegment(action.projectId, action.data);
            break;
        case Actions.REMOVE_SEGMENT:
            controller.removeSegment(action.projectId, action.id);
            break;
        default:
    }
});
controller.store = store;
module.exports = controller.store;
