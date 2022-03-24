const BaseStore = require('./base/_store');
const OrganisationStore = require('./organisation-store');
const data = require('../data/base/_data');
const { env } = require('../../.eslintrc');

const createdFirstFeature = false;
const pageSize = 50;
const controller = {

    getChangeRequests: (envId, page) => {
        store.loading();
        store.envId = envId;
        const endpoint = (page && `${page}${`&page_size=${pageSize}`}`) || `${Project.api}environments/${envId}/list-change-requests?page_size=${pageSize}`;
        data.get(endpoint)
            .then((res) => {
                store.model[envId] = res;
                store.loaded();
            });
    },
    updateChangeRequest: (changeRequest) => {
        store.loading();
        data.put(`${Project.api}features/workflows/change-requests/${changeRequest.id}/`,changeRequest)
            .then((res) => {
                store.model[changeRequest.id] = res;
                store.loaded();
            });
    },
    getChangeRequest: (id) => {
        store.loading();
        data.get(`${Project.api}features/workflows/change-requests/${id}/`)
            .then((res) => {
                store.model[id] = res;
                store.loaded();
            });
    },
};


const store = Object.assign({}, BaseStore, {
    id: 'change-request-store',
    model: {},
    pageSize,
});


store.dispatcherIndex = Dispatcher.register(store, (payload) => {
    const action = payload.action; // this is our action from handleViewAction
    switch (action.actionType) {
        case Actions.GET_CHANGE_REQUESTS:
            controller.getChangeRequests(action.environment, action.page);
            break;
        case Actions.GET_CHANGE_REQUEST:
            controller.getChangeRequest(action.id);
            break;
        case Actions.UPDATE_CHANGE_REQUEST:
            controller.updateChangeRequest(action.changeRequest);
            break;
    }
});
controller.store = store;
module.exports = controller.store;
