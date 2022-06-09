const BaseStore = require('./base/_store');
const data = require('../data/base/_data');


const controller = {
    getAuditLog: (page, projectId, environmentId) => {
        const PAGE_SIZE = flagsmith.hasFeature("audit_api_search")? flagsmith.getValue("audit_api_search")||999 :999;

        store.loading();
        let endpoint = ((page && `${page}${store.search ? `&search=${store.search}&project=${projectId}` : `&project=${projectId}`}`) || `${Project.api}audit/${store.search ? `?search=${store.search}&project=${projectId}` : `?project=${projectId}`}`);
        if (environmentId) {
            endpoint  += `&environments=${environmentId}`
        }
        endpoint = endpoint + `&page_size=${PAGE_SIZE}`
        data.get(endpoint)
            .then((res) =>{
                const key = `${environmentId||projectId}`
                store.model = store.model||{}
                store.model[key] = res && res.results;
                store.paging[key] = {}
                store.paging[key].next = res.next;
                store.paging[key].count = res.count;
                store.paging[key].previous = res.previous;
                store.paging[key].currentPage = endpoint.indexOf('?page=') !== -1 ? parseInt(endpoint.substr(endpoint.indexOf('?page=') + 6)) : 1;
                store.loaded();
            });
    },
    searchAuditLog: _.throttle((search, projectId, environmentId) => {
        store.search = search;
        controller.getAuditLog(0, projectId, environmentId);
    }, 1000),
};


const store = Object.assign({}, BaseStore, {
    id: 'identitylist',
    paging: {
    },
    getPaging() {
        return {
            ...store.paging,
            pageSize: flagsmith.hasFeature("audit_api_search")?flagsmith.getValue("audit_api_search")||999 :999
        };
    },
});


store.dispatcherIndex = Dispatcher.register(store, (payload) => {
    const action = payload.action; // this is our action from handleViewAction

    switch (action.actionType) {
        case Actions.GET_AUDIT_LOG:
            store.search = action.search || '';
            controller.getAuditLog(null, action.projectId, action.environmentId);
            break;
        case Actions.GET_AUDIT_LOG_PAGE:
            controller.getAuditLog(action.page, action.projectId, action.environmentId);
            break;
        case Actions.SEARCH_AUDIT_LOG:
            controller.searchAuditLog(action.search, action.projectId,action.environmentId);
            break;
        default:
    }
});

controller.store = store;
module.exports = controller.store;
