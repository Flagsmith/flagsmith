const BaseStore = require('./base/_store');
const OrganisationStore = require('./organisation-store');
const data = require('../data/base/_data');

const PAGE_SIZE = 2;

const controller = {

    getSegments: (projectId, environmentId, page) => {
        store.loading();
        store.envId = environmentId;
        const endpoint = page || `${Project.api}projects/${projectId}/segments/?page_size=${PAGE_SIZE}&q=${encodeURIComponent(store.search || '')}`;
        data.get(endpoint)
            .then((res) => {
                store.model = res.results && _.sortBy(res.results, 'name');
                store.paging.next = res.next;
                store.paging.count = res.count;
                store.paging.previous = res.previous;
                store.loaded();
            });
    },
    searchSegments: _.throttle((projectId, environmentId, search) => {
        store.search = search;
        controller.getSegments(projectId, environmentId, null);
    }, 1000),
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
            .then(() => {
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
            .then(() => {
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


const store = Object.assign({}, BaseStore, {
    id: 'segments',
    PAGE_SIZE,
    paging: {
        pageSize: PAGE_SIZE,
    },
    getSegments() {
        return store.model;
    },
});


store.dispatcherIndex = Dispatcher.register(store, (payload) => {
    const action = payload.action; // this is our action from handleViewAction

    switch (action.actionType) {
        case Actions.GET_SEGMENTS:
            store.search = '';
            controller.getSegments(action.projectId, action.environmentId);
            break;
        case Actions.GET_SEGMENTS_PAGE:
            controller.getSegments(action.projectId, action.environmentId, action.page);
            break;
        case Actions.SEARCH_SEGMENTS:
            controller.searchSegments(action.projectId, action.environmentId, action.search);
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
