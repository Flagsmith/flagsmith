const BaseStore = require('./base/_store');
const OrganisationStore = require('./organisation-store');
const data = require('../data/base/_data');
const { env } = require('../../.eslintrc');

const PAGE_SIZE = 20;
const createdFirstFeature = false;
const controller = {

    actionChangeRequest: (id, action, cb) => {
        store.loading();
        data.post(`${Project.api}features/workflows/change-requests/${id}/${action}/`)
            .then((res) => {
                data.get(`${Project.api}features/workflows/change-requests/${id}/`)
                    .then((res) => {
                        store.model[id] = res;
                        cb && cb();
                        store.loaded();
                    });
            }).catch(e => API.ajaxHandler(store, e));
    },
    getChangeRequests: (envId, { committed, live_from_after }, page) => {
        store.loading();
        store.envId = envId;
        let endpoint = page || `${Project.api}environments/${envId}/list-change-requests/?${committed ? 'committed=1' : 'committed=1'}${live_from_after ? `&live_from_after=${live_from_after}` : ''}`;
        if (!endpoint.includes('page_size')) {
            endpoint += `&page_size=${PAGE_SIZE}/`;
        }
        data.get(endpoint)
            .then((res) => {
                res.currentPage = page ? parseInt(page.split('page=')[1]) : 1;
                res.pageSize = PAGE_SIZE;
                if (live_from_after) {
                    store.scheduled[envId] = res;
                } else if (committed) {
                    store.committed[envId] = res;
                } else {
                    store.model[envId] = res;
                }
                store.loaded();
            }).catch(e => API.ajaxHandler(store, e));
    },
    deleteChangeRequest: (id, cb) => {
        store.loading();
        data.delete(`${Project.api}features/workflows/change-requests/${id}/`)
            .then((res) => {
                store.loaded();
                cb();
            }).catch(e => API.ajaxHandler(store, e));
    },
    updateChangeRequest: (changeRequest) => {
        store.loading();
        data.put(`${Project.api}features/workflows/change-requests/${changeRequest.id}/`, changeRequest)
            .then((res) => {
                store.model[changeRequest.id] = res;
                store.loaded();
            }).catch(e => API.ajaxHandler(store, e));
    },
    getChangeRequest: (id) => {
        store.loading();
        data.get(`${Project.api}features/workflows/change-requests/${id}/`)
            .then((res) => {
                store.model[id] = res;
                store.loaded();
            }).catch(e => API.ajaxHandler(store, e));
    },
};


const store = Object.assign({}, BaseStore, {
    id: 'change-request-store',
    model: {},
    committed: {},
    scheduled: {},
});


store.dispatcherIndex = Dispatcher.register(store, (payload) => {
    const action = payload.action; // this is our action from handleViewAction
    switch (action.actionType) {
        case Actions.GET_CHANGE_REQUESTS:
            controller.getChangeRequests(action.environment, { committed: action.committed, live_from_after: action.live_from_after }, action.page);
            break;
        case Actions.GET_CHANGE_REQUEST:
            controller.getChangeRequest(action.id);
            break;
        case Actions.UPDATE_CHANGE_REQUEST:
            controller.updateChangeRequest(action.changeRequest);
            break;
        case Actions.DELETE_CHANGE_REQUEST:
            controller.deleteChangeRequest(action.id, action.cb);
            break;
        case Actions.ACTION_CHANGE_REQUEST:
            controller.actionChangeRequest(action.id, action.action, action.cb);
            break;
    }
});
controller.store = store;
module.exports = controller.store;
