const BaseStore = require('./base/_store');


const controller = {

    getEnvironment: (id) => {
        if (!store.model) { // todo: change logic a bit
            store.loading();

            fetch(`${Project.api}environments/${id}/`, {
                headers: {
                    'FFVERSIONKEY': id,
                },
            }).then(res => res.json())
                .then((res) => {
                    store.model = Object.assign(res, {
                        id,
                    });
                    store.loaded();
                });
        }
    },
    saveEnvironment: (env) => {
        store.saving();
        setTimeout(() => {
            store.model = env;
            store.saved();
        }, 2000);
    },
    updateSelection(data) {
        store.selection = data;
        store.trigger('change');
        store.trigger('selected');
    },
};


var store = Object.assign({}, BaseStore, {
    id: 'account',
    getFlagsForEditing() {
        return store.model && store.model.featurestates && store.model.featurestates.concat([]).map(e => Object.assign({}, e));// immutable flags
    },
    getSelection() {
        return store.selection || {};
    },
});


store.dispatcherIndex = Dispatcher.register(store, (payload) => {
    const action = payload.action; // this is our action from handleViewAction

    switch (action.actionType) {
        case Actions.GET_ENVIRONMENT:
            controller.getEnvironment(action.id, action.user);
            break;
        case Actions.SELECT_ENVIRONMENT:
            controller.updateSelection(action.data);
            break;
        default:
    }
});
controller.store = store;
module.exports = controller.store;
