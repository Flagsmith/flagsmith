const BaseStore = require('./base/_store');
const data = require('../data/base/_data');

const PAGE_SIZE = 10;

const controller = {
    getIdentities: (envId, page, pageSize, pageType) => {
        store.loading();
        store.envId = envId;
        const endpoint = (page && `${page}${store.search ? `&q=${encodeURIComponent(store.search)}&page_size=${pageSize || PAGE_SIZE}` : `&page_size=${pageSize || PAGE_SIZE}`}`) || `${Project.api}environments/${envId}/${Utils.getIdentitiesEndpoint()}/${store.search ? `?q=${encodeURIComponent(store.search)}&page_size=${pageSize || PAGE_SIZE}` : `?page_size=${pageSize || PAGE_SIZE}`}`;

        data.get(endpoint)
            .then((res) => {


                store.model = res && res.results && res.results.map((v)=>{
                    if (v.id) {
                        return v
                    }
                    return {
                        ...v,
                        id: v.identity_uuid
                    }
                });
                store.paging.next = res.next;
                store.paging.count = res.count;
                store.paging.previous = res.previous;
                if (Utils.getIsEdge()) {

                    if (!pageType) {
                        store.paging = [endpoint]
                    } else if (store.current) {
                        
                    }


                    //
                    if (pageType === "PREVIOUS") {
                        store.paging.slice(0,-1)
                    } else if (pageType === "NEXT") {
                        store.paging.push(endpoint)
                    } else


                    const params = Utils.fromParam(store.paging[store.paging.length-1])
                    store.paging.next =
                    store.paging.previous = `${store.paging[store.paging.length-1]}`
                }
                store.paging.currentPage = endpoint.indexOf('?page=') !== -1 ? parseInt(endpoint.substr(endpoint.indexOf('?page=') + 6)) : 1;
                store.loaded();
            });
    },
    saveIdentity: (id, identity) => {
        store.saving();
        setTimeout(() => {
            const index = _.findIndex(store.model, { id });
            store.model[index] = identity;
            store.saved();
        }, 2000);
    },
    searchIdentities: _.throttle((envId, search, pageSize) => {
        store.search = search;
        controller.getIdentities(envId, null, pageSize);
    }, 1000),
    deleteIdentity: (envId, id) => {
        store.saving();
        data.delete(`${Project.api}environments/${envId}/${Utils.getIdentitiesEndpoint()}/${id}/`)
            .then(() => {
                const index = _.findIndex(store.model, identity => identity.id === id);
                if (index !== -1) {
                    store.model.splice(index, 1);
                }
                store.saved();
            })
            .catch(e => API.ajaxHandler(store, e));
    },
};


const store = Object.assign({}, BaseStore, {
    id: 'identitylist',
    pages: [],
    paging: {
        pageSize: PAGE_SIZE,
    },
    getIdentityForEditing(id) {
        return store.model && _.cloneDeep(_.find(store.model, { id })); // immutable
    },
    getPaging() {
        return store.paging;
    },
});


store.dispatcherIndex = Dispatcher.register(store, (payload) => {
    const action = payload.action; // this is our action from handleViewAction

    switch (action.actionType) {
        case Actions.GET_IDENTITIES:
            store.search = '';
            controller.getIdentities(action.envId, null, action.pageSize);
            break;
        case Actions.SAVE_IDENTITY:
            controller.saveIdentity(action.id, action.identity);
            break;
        case Actions.GET_IDENTITIES_PAGE:
            controller.getIdentities(action.envId, action.page, null, action.pageType);
            break;
        case Actions.SEARCH_IDENTITIES:
            controller.searchIdentities(action.envId, action.search, action.pageSize);
            break;
        case Actions.DELETE_IDENTITY:
            controller.deleteIdentity(action.envId, action.id);
            break;
        default:
    }
});
controller.store = store;
module.exports = controller.store;
