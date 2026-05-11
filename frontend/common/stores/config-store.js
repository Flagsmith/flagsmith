import Project from 'common/project'
import Dispatcher from 'common/dispatcher/dispatcher'
import BaseStore from './base/_store'

window.Project = Project

const controller = {
  get() {
    store.loading()
  },
  loaded(oldFlags) {
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

flagsmith
  .init({
    AsyncStorage,
    api: Project.flagsmithClientAPI,
    cacheFlags: true,
    enableAnalytics: window.E2E ? false : Project.flagsmithAnalytics,
    environmentID: Project.flagsmith,
    onChange: controller.loaded,
    realtime: window.E2E ? false : Project.flagsmithRealtime,
    ...(Project.evaluationAnalyticsServerUrl
      ? {
          evaluationAnalyticsConfig: {
            analyticsServerUrl: Project.evaluationAnalyticsServerUrl,
          },
        }
      : {}),
  })
  .catch(() => {
    controller.onError()
  })

controller.store = store
export default controller.store
