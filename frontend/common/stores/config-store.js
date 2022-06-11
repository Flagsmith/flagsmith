const BaseStore = require('./base/_store');
window.Project = require('../project');

window.Project = {
    ...window.Project,
    ...projectOverrides, // environment.js (also app.yaml if using app engine)
};
const controller = {
    get() {
        store.loading();
    },
    onError() {
        store.error = true;
        store.goneABitWest();
    },
    loaded(oldFlags) { // Occurs whenever flags are changed
        if (Utils.getFlagsmithHasFeature('dark_mode')) {
            document.body.classList.add('dark');
        }
        if (!oldFlags || !Object.keys(oldFlags).length) {
            store.loaded();
        } else {
            store.changed();
        }
        store.model = flagsmith.getAllFlags();
    },
};


const store = Object.assign({}, BaseStore, {
    id: 'config',
});


store.dispatcherIndex = Dispatcher.register(store, (payload) => {
    const action = payload.action; // this is our action from	handleViewAction

    switch (action.actionType) {
        case Actions.GET_CONFIG:
            controller.get();
            break;
        default:
            break;
    }
});

flagsmith.init({
    environmentID: Project.flagsmith,
    onChange: controller.loaded,
    api: Project.flagsmithClientAPI,
    cacheFlags: true,
    AsyncStorage,
    enableAnalytics: projectOverrides.flagsmithAnalytics,
}).catch(() => {
    controller.onError();
});

controller.store = store;
module.exports = controller.store;
