const BaseStore = require('./base/_store');
const data = require('../data/base/_data');

const PAGE_SIZE = 999;

const controller = {
    getAuditLog: (page, projectId) => {
        store.loading();
        const endpoint = ((page && `${page}${store.search ? `&q=${store.search}&project=${projectId}` : `&project=${projectId}`}`) || `${Project.api}audit/${store.search ? `?q=${store.search}&project=${projectId}` : `?project=${projectId}`}`);
        data.get(endpoint)
            .then((res) => {
                store.model = res && res.results;
                store.paging.next = res.next;
                store.paging.count = res.count;
                store.paging.previous = res.previous;
                store.paging.currentPage = endpoint.indexOf('?page=') !== -1 ? parseInt(endpoint.substr(endpoint.indexOf('?page=') + 6)) : 1;
                store.loaded();
            });
    },
    searchAuditLog: _.throttle((search) => {
        store.search = search;
        controller.getAuditLog();
    }, 1000),
};


const store = Object.assign({}, BaseStore, {
    id: 'identitylist',
    paging: {
        pageSize: PAGE_SIZE,
    },
    getPaging() {
        return store.paging;
    },
});


store.dispatcherIndex = Dispatcher.register(store, (payload) => {
    const action = payload.action; // this is our action from handleViewAction

    switch (action.actionType) {
        case Actions.GET_AUDIT_LOG:
            store.search = '';
            controller.getAuditLog(null, action.projectId);
            break;
        case Actions.GET_AUDIT_LOG_PAGE:
            controller.getAuditLog(action.page, action.projectId);
            break;
        case Actions.SEARCH_AUDIT_LOG:
            controller.searchAuditLog(action.search, action.projectId);
            break;
        default:
    }
});

controller.store = store;
module.exports = controller.store;
