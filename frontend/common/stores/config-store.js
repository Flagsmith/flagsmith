import Project from 'common/project';
const Dispatcher = require('../dispatcher/dispatcher');
const BaseStore = require('./base/_store');
window.Project = require('../project');

const controller = {
    get() {
        store.loading();
    },
    onError() {
        store.error = true;
        store.goneABitWest();
    },
    loaded(oldFlags) { // Occurs whenever flags are changed
        if (flagsmith.hasFeature('dark_mode')) {
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
    const action = payload.action; // this is our action from handleViewAction

    switch (action.actionType) {
        default:
            break;
    }
});

flagsmith.init({
    environmentID: Project.flagsmith,
    onChange: controller.loaded,
    api: Project.flagsmithClientAPI,
    cacheFlags: true,
    realtime: true,
    AsyncStorage,
    enableAnalytics: Project.flagsmithAnalytics,
}).catch(() => {
    controller.onError();
});

controller.store = store;
module.exports = controller.store;

