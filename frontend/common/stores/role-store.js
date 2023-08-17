const Dispatcher = require('../dispatcher/dispatcher')
const BaseStore = require('./base/_store')
const data = require('../data/base/_data')

const controller = {
  getRoles: (organisationId) => {
    store.loading()
    const endpoint = `http://localhost:8000/api/v1/organisations/${organisationId}/roles/`
    return data
      .get(endpoint)
      .then((res) => {
        store.paging.next = res.next
        store.paging.count = res.count
        store.paging.previous = res.previous
        store.paging.currentPage =
          endpoint.indexOf('?page=') !== -1
            ? parseInt(endpoint.substr(endpoint.indexOf('?page=') + 6))
            : 1
        store.model.roles = res.results && _.sortBy(res.results, (r) => r.name)
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
        console.log('DEBUG: res:', res)
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
