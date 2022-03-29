const BaseStore = require('./base/_store');
const data = require('../data/base/_data');


const controller = {
    getIdentitySegments: (projectId, id, page) => {
        store.loading();
        const endpoint = page || `${Project.api}projects/${projectId}/segments/?identity=${id}`;
        return data.get(endpoint)
            .then((res) => {
                store.model[id] = res.results && _.sortBy(res.results, r => r.name);
                store.paging.next = res.next;
                store.paging.count = res.count;
                store.paging.previous = res.previous;
                store.paging.currentPage = endpoint.indexOf('?page=') !== -1 ? parseInt(endpoint.substr(endpoint.indexOf('?page=') + 6)) : 1;
                store.loaded();
            })
            .catch(e => API.ajaxHandler(store, e));
    },
};


const store = Object.assign({}, BaseStore, {
    id: 'identity-segments',
    paging: {},
    model: {},
});

store.dispatcherIndex = Dispatcher.register(store, (payload) => {
    const action = payload.action; // this is our action from	handleViewAction
    switch (action.actionType) {
        case Actions.GET_IDENTITY_SEGMENTS:
            controller.getIdentitySegments(action.projectId, action.id);
            break;
        case Actions.GET_IDENTITY_SEGMENTS_PAGE:
            controller.getIdentitySegments(null, null, action.page);
            break;
        default:
    }
});
controller.store = store;
module.exports = controller.store;
