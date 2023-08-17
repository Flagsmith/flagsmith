const Dispatcher = require('../dispatcher/dispatcher')
const BaseStore = require('./base/_store')
const data = require('../data/base/_data')
const { getRoles } = require('../services/useRole')
const { getStore } = require('../store')

const controller = {
  getRoles: (organisationId) => {
    store.loading()
    return getRoles(
      getStore(),
      { organisation_id: `${organisationId}` },
      { forceRefetch: true },
    )
      .then((res) => {
        store.paging.next = res.data.next
        store.paging.count = res.data.count
        store.paging.previous = res.data.previous
        store.model.roles = res.data.results && _.sortBy(res.data.results, (r) => r.name)
        store.loaded()
      })
      .catch((e) => API.ajaxHandler(store, e))
  },
  getRole: (organisationId, roleId) => {
    store.loading()
    const endpoint = `http://localhost:8000/api/v1/organisations/${organisationId}/roles/${roleId}`
    return data
      .get(endpoint)
      .then((res) => {
        store.loaded()
      })
      .catch((e) => API.ajaxHandler(store, e))
  },
}
const store = Object.assign({}, BaseStore, {
  getRoles() {
    return store.model && store.model.roles
  },
  model: {},
  paging: {},
  roles: [],
})

store.dispatcherIndex = Dispatcher.register(store, (payload) => {
  const action = payload.action // this is our action from handleViewAction
  switch (action.actionType) {
    case Actions.GET_ROLES:
      controller.getRoles(action.organisationId)
      break
    default:
    // Handle other actions if needed
  }
})

controller.store = store
module.exports = controller.store
