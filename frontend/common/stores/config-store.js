import Project from 'common/project'

const Dispatcher = require('../dispatcher/dispatcher')
const BaseStore = require('./base/_store')
window.Project = require('../project')

const controller = {
  get() {
    store.loading()
  },
  loaded(oldFlags) {
    // Occurs whenever flags are changed
    if (flagsmith.hasFeature('dark_mode')) {
      document.body.classList.add('dark')
    }
    if (!oldFlags || !Object.keys(oldFlags).length) {
      store.loaded()
    } else {
      store.changed()
    }
    store.model = flagsmith.getAllFlags()
  },
  onError() {
    store.error = true
    store.goneABitWest()
  },
}

const store = Object.assign({}, BaseStore, {
  id: 'config',
})

store.dispatcherIndex = Dispatcher.register(store, (payload) => {
  const action = payload.action // this is our action from handleViewAction

  switch (action.actionType) {
    default:
      break
  }
})

console.log(Project)
let state = undefined
try {
  // If a flagsmith.json file
  let state = require('../../flagsmith.json')
} catch (e) {}
if (
  !(
    state.api === Project.flagsmithClientAPI &&
    state.environmentID === Project.flagsmith
  )
) {
  console.error(
    'Mismatch between compiled flagsmith JSON and expected environment/keys',
  )
  state = undefined
}
flagsmith
  .init({
    AsyncStorage,
    api: Project.flagsmithClientAPI,
    cacheFlags: true,
    enableAnalytics: Project.flagsmithAnalytics,
    environmentID: Project.flagsmith,
    onChange: controller.loaded,
    preventFetch: !!state,
    realtime: true,
    state,
  })
  .catch(() => {
    controller.onError()
  })

controller.store = store
module.exports = controller.store
