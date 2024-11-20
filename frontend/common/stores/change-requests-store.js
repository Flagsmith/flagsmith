const Dispatcher = require('../dispatcher/dispatcher')
const BaseStore = require('./base/_store')
const data = require('../data/base/_data')
const { flatten } = require('lodash')
const {
  addFeatureSegmentsToFeatureStates,
} = require('../services/useFeatureState')
const { environmentService } = require('common/services/useEnvironment')
const { changeRequestService } = require('common/services/useChangeRequest')
const { getStore } = require('common/store')

const PAGE_SIZE = 20
const transformChangeRequest = async (changeRequest) => {
  const feature_states = await Promise.all(
    changeRequest.feature_states.map(addFeatureSegmentsToFeatureStates),
  )

  return {
    ...changeRequest,
    feature_states,
  }
}
const controller = {
  actionChangeRequest: (id, action, cb) => {
    store.loading()
    data
      .post(`${Project.api}features/workflows/change-requests/${id}/${action}/`)
      .then(() => {
        data
          .get(`${Project.api}features/workflows/change-requests/${id}/`)
          .then(async (res) => {
            store.model[id] = await transformChangeRequest(res)
            getStore().dispatch(
              changeRequestService.util.invalidateTags(['ChangeRequest']),
            )
            cb && cb()
            store.loaded()
          })
      })
      .catch((e) => API.ajaxHandler(store, e))
  },
  deleteChangeRequest: (id, cb) => {
    store.loading()
    data
      .delete(`${Project.api}features/workflows/change-requests/${id}/`)
      .then(() => {
        store.loaded()
        getStore().dispatch(
          changeRequestService.util.invalidateTags(['ChangeRequest']),
        )
        cb()
      })
      .catch((e) => API.ajaxHandler(store, e))
  },
  getChangeRequest: (id, projectId, environmentId) => {
    store.loading()
    data
      .get(`${Project.api}features/workflows/change-requests/${id}/`)
      .then(async (apiResponse) => {
        const res = await transformChangeRequest(apiResponse)
        const feature =
          res.feature_states[0]?.feature || res.change_sets[0]?.feature
        return Promise.all([
          data.get(
            `${Project.api}environments/${environmentId}/featurestates/?feature=${feature}`,
          ),
          data.get(`${Project.api}projects/${projectId}/features/${feature}/`),
        ]).then(([environmentFlag, projectFlag]) => {
          store.model[id] = res
          store.flags[id] = {
            environmentFlag: environmentFlag.results[0],
            projectFlag,
          }
          store.loaded()
        })
      })
      .catch((e) => API.ajaxHandler(store, e))
  },
  updateChangeRequest: (changeRequest) => {
    store.loading()
    data
      .get(
        `${Project.api}features/workflows/change-requests/${changeRequest.id}/`,
      )
      .then((res) => {
        data
          .put(
            `${Project.api}features/workflows/change-requests/${changeRequest.id}/`,
            {
              ...res,
              approvals: changeRequest.approvals,
              description: changeRequest.description,
              environment_feature_versions:
                changeRequest?.environment_feature_versions?.map((v) => v.uuid),
              group_assignments: changeRequest.group_assignments,
              title: changeRequest.title,
            },
          )
          .then(async () => {
            const res = await data.get(
              `${Project.api}features/workflows/change-requests/${changeRequest.id}/`,
            )
            store.model[changeRequest.id] = await transformChangeRequest(res)
            getStore().dispatch(
              changeRequestService.util.invalidateTags(['ChangeRequest']),
            )
            store.loaded()
          })
          .catch((e) => API.ajaxHandler(store, e))
      })
  },
}

const store = Object.assign({}, BaseStore, {
  committed: {},
  flags: {},
  id: 'change-request-store',
  model: {},
  scheduled: {},
})

store.dispatcherIndex = Dispatcher.register(store, (payload) => {
  const action = payload.action // this is our action from handleViewAction
  switch (action.actionType) {
    case Actions.GET_CHANGE_REQUEST:
      controller.getChangeRequest(
        action.id,
        action.projectId,
        action.environmentId,
      )
      break
    case Actions.UPDATE_CHANGE_REQUEST:
      controller.updateChangeRequest(action.changeRequest)
      break
    case Actions.DELETE_CHANGE_REQUEST:
      controller.deleteChangeRequest(action.id, action.cb)
      break
    case Actions.ACTION_CHANGE_REQUEST:
      controller.actionChangeRequest(action.id, action.action, action.cb)
      break
    default:
      break
  }
})
controller.store = store
module.exports = controller.store
