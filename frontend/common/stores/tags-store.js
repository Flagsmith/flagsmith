import _data from '../data/base/_data';

const BaseStore = require('./base/_store');

const controller = {
    get(projectId) {
        store.loading();
        _data.get(`${Project.api}projects/${projectId}/tags/`)
            .then((res) => {
                store.model[projectId] = res.results;
                store.loaded();
            })
            .catch(e => API.ajaxHandler(store, e));
    },
    update(projectId, data, onComplete) {
        store.saving();
        const index = _.findIndex(store.model[projectId], { id: data.id });
        _data.put(`${Project.api}projects/${projectId}/tags/${data.id}/`, data)
            .then((res) => {
                if (index !== -1) {
                    store.model[projectId][index] = res;
                }
                onComplete && onComplete(data);
                store.saved();
            })
            .catch(e => API.ajaxHandler(store, e));
    },
    delete(projectId, data, onComplete) {
        store.saving();
        _data.delete(`${Project.api}projects/${projectId}/tags/${data.id}/`)
            .then(() => {
                store.model[projectId] = _.filter(store.model[projectId], tag => tag.id !== data.id);
                onComplete && onComplete(data);
                store.saved();
            })
            .catch(e => API.ajaxHandler(store, e));
    },
    create(projectId, data, onComplete) {
        store.saving();
        _data.post(`${Project.api}projects/${projectId}/tags/`, { ...data, description: data.description || 'Description' })
            .then((res) => {
                store.model[projectId].push(res);
                onComplete && onComplete(store.model[projectId][store.model[projectId].length - 1]);
                store.loaded();
            })
            .catch(e => API.ajaxHandler(store, e));

        store.saved();
    },
};


const store = Object.assign({}, BaseStore, {
    id: 'tags',
    model: {},
    getTags: projectId => store.model[projectId],
    hasProtectedTag: (projectFlag, projectId) => {
        const tags = projectFlag && projectFlag.tags;
        if (tags && store.model) {

            return tags.find((id) => {
                const tag = store.model[projectId] && store.model[projectId].find(tag => tag.id === id);
                if (tag) {
                    const label = tag.label.toLowerCase().replace(/[ _]/g, '');
                    return label === 'protected' || 'donotdelete' || label === 'permanent';
                }
            });
        }
    },
});


store.dispatcherIndex = Dispatcher.register(store, (payload) => {
    const action = payload.action; // this is our action from	handleViewAction

    switch (action.actionType) {
        case Actions.GET_TAGS:
            controller.get(action.projectId);
            break;
        case Actions.UPDATE_TAG:
            controller.update(action.projectId, action.data, action.onComplete);
            break;
        case Actions.DELETE_TAG:
            controller.delete(action.projectId, action.data, action.onComplete);
            break;
        case Actions.CREATE_TAG:
            controller.create(action.projectId, action.data, action.onComplete);
            break;
        default:
            break;
    }
});

controller.store = store;
module.exports = controller.store;
