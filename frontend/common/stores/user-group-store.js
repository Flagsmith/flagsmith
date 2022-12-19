const BaseStore = require('./base/_store');
const data = require('../data/base/_data');

const PAGE_SIZE = 999;

const controller = {
    getGroups: (orgId, page) => {
        store.loading();
        store.orgId = orgId;
        const endpoint = (page && `${page}`) || `${Project.api}organisations/${orgId}/groups/`;
        data.get(endpoint)
            .then((res) => {
                store.model = res && res.results;
                store.paging.next = res.next;
                store.paging.count = res.count;
                store.paging.previous = res.previous;
                store.paging.currentPage = endpoint.indexOf('?page=') !== -1 ? parseInt(endpoint.substr(endpoint.indexOf('?page=') + 6)) : 1;
                store.loaded();
                store.saved();
            });
    },
    createGroup: (orgId, group) => {
        store.saving();
        data.post(`${Project.api}organisations/${orgId}/groups/`, group)
            .then((res) => {
                let prom = Promise.resolve();
                if (group.users) {
                    prom = data.post(`${Project.api}organisations/${orgId}/groups/${res.id}/add-users/`, { user_ids: group.users.map(u => u.id) })
                }
                prom.then(() => {
                    controller.getGroups(orgId);
                });
            })
            .catch(e => API.ajaxHandler(store, e));
    },
    updateGroup: (orgId, group) => {
        store.saving();
        data.put(`${Project.api}organisations/${orgId}/groups/${group.id}/`, group).then((currentGroup)=>{
            const toRemove = group.usersToRemove.filter((toRemove)=>{
                return !!currentGroup.users.find((user)=>user.id === toRemove.id)
            })
            const toAdd = group.users.filter((toRemove)=>{
                return !currentGroup.users.find((user)=>user.id === toRemove.id)
            })

            Promise.all([
                data.post(`${Project.api}organisations/${orgId}/groups/${group.id}/add-users/`, { user_ids: toAdd.map(u => u.id) }),
                data.post(`${Project.api}organisations/${orgId}/groups/${group.id}/remove-users/`, { user_ids: toRemove.map(u => u.id) }),
            ]).then(() => {
                controller.getGroups(orgId);
            })
        })

            .catch(e => API.ajaxHandler(store, e));
    },
    deleteGroup: (orgId, group) => {
        store.saving();
        data.delete(`${Project.api}organisations/${orgId}/groups/${group}/`)
            .then(() => {
                controller.getGroups(orgId);
            })
            .catch(e => API.ajaxHandler(store, e));
    },
};


const store = Object.assign({}, BaseStore, {
    id: 'identitylist',
    paging: {
        pageSize: PAGE_SIZE,
    },
    getGroupsForEditing(id) {
        return store.model && _.cloneDeep(_.find(store.model, { id })); // immutable
    },
    getPaging() {
        return store.paging;
    },
});


store.dispatcherIndex = Dispatcher.register(store, (payload) => {
    const action = payload.action; // this is our action from handleViewAction

    switch (action.actionType) {
        case Actions.GET_GROUPS:
            store.search = '';
            controller.getGroups(action.orgId);
            break;
        case Actions.UPDATE_GROUP:
            controller.updateGroup(action.orgId, action.data);
            break;
        case Actions.CREATE_GROUP:
            controller.createGroup(action.orgId, action.data);
            break;
        case Actions.GET_GROUPS_PAGE:
            controller.getGroups(action.page);
            break;
        case Actions.DELETE_GROUP:
            controller.deleteGroup(action.orgId, action.data);
            break;
        default:
    }
});
controller.store = store;
module.exports = controller.store;
