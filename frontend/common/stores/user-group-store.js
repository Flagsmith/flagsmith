const Dispatcher = require('../dispatcher/dispatcher')
const BaseStore = require('./base/_store')
const data = require('../data/base/_data')
const {
  createGroupAdmin,
  deleteGroupAdmin,
  getGroups,
} = require('../services/useGroup')
const { getStore } = require('../store')

const PAGE_SIZE = 999

const controller = {
  createGroup: (orgId, group) => {
    store.saving()
    data
      .post(`${Project.api}organisations/${orgId}/groups/`, group)
      .then((res) => {
        let prom = Promise.resolve()
        if (group.users) {
          prom = data.post(
            `${Project.api}organisations/${orgId}/groups/${res.id}/add-users/`,
            { user_ids: group.users.map((u) => u.id) },
          )
        }
        prom.then(() => {
          controller.getGroups(orgId)
        })
      })
      .catch((e) => API.ajaxHandler(store, e))
  },
  getGroups: (orgId, page) => {
    store.loading()
    getGroups(getStore(), { orgId, page: 1 }).then(() => {
      store.loaded()
      store.saved()
    })
  },
  updateGroup: (orgId, group) => {
    store.saving()
    data
      .put(`${Project.api}organisations/${orgId}/groups/${group.id}/`, group)
      .then((currentGroup) => {
        const toRemove = group.usersToRemove.filter(
          (toRemove) =>
            !!currentGroup.users.find((user) => user.id === toRemove.id),
        )
        const toAdd = group.users.filter(
          (toRemove) =>
            !currentGroup.users.find((user) => user.id === toRemove.id),
        )

        Promise.all([
          data.post(
            `${Project.api}organisations/${orgId}/groups/${group.id}/add-users/`,
            { user_ids: toAdd.map((u) => u.id) },
          ),
          data.post(
            `${Project.api}organisations/${orgId}/groups/${group.id}/remove-users/`,
            { user_ids: toRemove.map((u) => u.id) },
          ),
        ]).then(() => {
          if (Utils.getFlagsmithHasFeature('group_admins')) {
            Promise.all(
              (group.usersToAddAdmin || [])
                .map((v) =>
                  createGroupAdmin(getStore(), {
                    group: group.id,
                    orgId,
                    user: v.id,
                  }),
                )
                .concat(
                  (group.usersToRemoveAdmin || []).map((v) =>
                    deleteGroupAdmin(getStore(), {
                      group: group.id,
                      orgId,
                      user: v.id,
                    }),
                  ),
                ),
            )
          }

          controller.getGroups(orgId)
        })
      })

      .catch((e) => API.ajaxHandler(store, e))
  },
}

const store = Object.assign({}, BaseStore, {
  getPaging() {
    return store.paging
  },
  id: 'identitylist',
  paging: {
    pageSize: PAGE_SIZE,
  },
})

store.dispatcherIndex = Dispatcher.register(store, (payload) => {
  const action = payload.action // this is our action from handleViewAction

  switch (action.actionType) {
    case Actions.UPDATE_GROUP:
      controller.updateGroup(action.orgId, action.data)
      break
    case Actions.CREATE_GROUP:
      controller.createGroup(action.orgId, action.data)
      break
    default:
  }
})
controller.store = store
module.exports = controller.store
