const BaseStore = require('./base/_store');
const data = require('../data/base/_data');
const OrganisationStore = require('../stores/organisation-store');

const controller = {

    getPermissions: (id, level) => {
        if (store.model[level] && store.model[level][id]) {
            return;
        }
        store.model[level] = store.model[level] || {};
        store.model[level][id] = store.model[level][id] || {};

        store.loading();
        data.get(`${Project.api}${level}s/${id}/my-permissions/`)
            .then((res) => {
                store.model[level][id] = store.model[level][id] || {};
                _.map(res.permissions, (p) => {
                    store.model[level][id][p] = true;
                });
                store.model[level][id].ADMIN = res.admin;
                store.changed();
            });
    },

    getAvailablePermissions: () => {
        if (store.model.availablePermissions.projects) {
            return;
        }
        Promise.all(['project', 'environment', 'organisation'].map(v => data.get(`${Project.api}${v}s/permissions/`)
            .then((res) => {
                store.model.availablePermissions[v] = res;
            }))).then(() => {
            store.loaded();
        });
    },

};


var store = Object.assign({}, BaseStore, {
    id: 'permissions',
    model: {
        availablePermissions: {

        },
    },
    getPermissions(id, level) {
        return store.model[level] && store.model[level][id];
    },
    getPermission(id, level, permission) {
        if (AccountStore.isAdmin()) {
            return true;
        }
        const perms = store.getPermissions(id, level);
        // return !!(perms && (perms[permission]));
        return (!!(perms && (perms[permission])) || (perms && perms.ADMIN));
    },
    getAvailablePermissions(level) {
        return store.model.availablePermissions[level];
    },
});


store.dispatcherIndex = Dispatcher.register(store, (payload) => {
    const action = payload.action; // this is our action from handleViewAction

    switch (action.actionType) {
        case Actions.GET_PERMISSIONS:
            controller.getPermissions(action.id, action.level);
            break;
        case Actions.GET_AVAILABLE_PERMISSIONS:
            controller.getAvailablePermissions();
            break;
        default:
    }
});
controller.store = store;
module.exports = controller.store;
