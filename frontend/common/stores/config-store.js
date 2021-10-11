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

const flags = {

};
const hasDefaultFlags = typeof window.defaultFlags !== 'undefined'
    && typeof window.defaultFlags.map !== 'undefined'; // if defaultFlags is an array, set the default flags
if (hasDefaultFlags) {
    window.defaultFlags.map((v) => {
        flags[v.feature.name] = {
            enabled: v.enabled,
            value: v.feature_state_value,
        };
    });
}

flagsmith.init({
    environmentID: Project.flagsmith,
    onChange: controller.loaded,
    preventFetch: !!flags.prevent_fetch, // if we set prevent_fetch on defaultFlags, users will not be identified
    defaultFlags: hasDefaultFlags && flags,
    api: Project.flagsmithClientAPI,
    enableAnalytics: projectOverrides.flagsmithAnalytics,
}).catch(() => {
    controller.onError();
});

controller.store = store;
module.exports = controller.store;
