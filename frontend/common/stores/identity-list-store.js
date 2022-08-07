const BaseStore = require('./base/_store');
const data = require('../data/base/_data');

const PAGE_SIZE = 10;

const pages = [
    null,
    "eyJlbnZpcm9ubWVudF9hcGlfa2V5IjogIjhLekVUZERlTVk3eGtxa1NrWTNHc2ciLCAiaWRlbnRpZmllciI6ICJEYW5pZWxfcmFuYWxsb0B5YWhvby5jb20iLCAiY29tcG9zaXRlX2tleSI6ICI4S3pFVGREZU1ZN3hrcWtTa1kzR3NnX0RhbmllbF9yYW5hbGxvQHlhaG9vLmNvbSJ9",
    "eyJlbnZpcm9ubWVudF9hcGlfa2V5IjogIjhLekVUZERlTVk3eGtxa1NrWTNHc2ciLCAiaWRlbnRpZmllciI6ICJhYXJub3V0QGxlbm92by5jb20iLCAiY29tcG9zaXRlX2tleSI6ICI4S3pFVGREZU1ZN3hrcWtTa1kzR3NnX2Fhcm5vdXRAbGVub3ZvLmNvbSJ9",
    "eyJlbnZpcm9ubWVudF9hcGlfa2V5IjogIjhLekVUZERlTVk3eGtxa1NrWTNHc2ciLCAiaWRlbnRpZmllciI6ICJhZG1pbkBkZXYubG9jYWwiLCAiY29tcG9zaXRlX2tleSI6ICI4S3pFVGREZU1ZN3hrcWtTa1kzR3NnX2FkbWluQGRldi5sb2NhbCJ9",

]
const findPage = (str) =>{
    if(!str) return 0
    const res = pages.findIndex((v)=>{
        return str.includes(v)
    })
    return res === -1? 0 : res
}
const controller = {
    getIdentities: (envId, page, pageSize, pageType) => {
        if (store.isLoading) return
        store.loading();
        store.envId = envId;
        let endpoint = (page && `${page}${store.search ? `&q=${encodeURIComponent(store.search)}&page_size=${pageSize || PAGE_SIZE}` : `&page_size=${pageSize || PAGE_SIZE}`}`) || `${Project.api}environments/${envId}/${Utils.getIdentitiesEndpoint()}/${store.search ? `?q=${encodeURIComponent(store.search)}&page_size=${pageSize || PAGE_SIZE}` : `?page_size=${pageSize || PAGE_SIZE}`}`;

        if (Utils.getIsEdge()) {
            if (!pageType) {
                store.pages = [];
            }
            if (pageType === 'PREVIOUS') {
                store.pages.splice(-1);
                endpoint = store.paging.previous;

            } else if (pageType === 'NEXT') {
                endpoint = store.paging.next;
            }


        }

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
                    const current_evaluated_key = Utils.fromParam(endpoint).last_evaluated_key;

                    if (pageType === 'NEXT') { // Push the requested key as history
                        store.pages.push(current_evaluated_key)
                    }

                    const next_evaluated_key =  res.last_evaluated_key;
                    const previous_evaluated_key = !store.pages.length ? null : store.pages[store.pages.length-2] || null;
                    const strippedUrl = endpoint.replace(/&last_evaluated_key.*/g,"")

                    store.paging.next = res.results && res.results.length === PAGE_SIZE ? strippedUrl + `&last_evaluated_key=${encodeURIComponent(next_evaluated_key)}` : null
                    store.paging.previous = store.pages.length >= 1 ? strippedUrl + (previous_evaluated_key?`&last_evaluated_key=${encodeURIComponent(previous_evaluated_key)}`:"") : pageType ==="NEXT"? strippedUrl: null
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
