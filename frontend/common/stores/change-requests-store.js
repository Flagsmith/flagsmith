const Dispatcher = require('../dispatcher/dispatcher')
const BaseStore = require('./base/_store')
const data = require('../data/base/_data')
const { flatten } = require('lodash')
const {
  addFeatureSegmentsToFeatureStates,
} = require('../services/useFeatureState')

const PAGE_SIZE = 20
const transformChangeRequest = async (changeRequest) => {
  const res = changeRequest?.environment_feature_versions?.length
    ? {
        ...changeRequest,
        feature_states: flatten(
          changeRequest.environment_feature_versions.map(
            (featureVersion) => featureVersion.feature_states,
          ),
        ),
      }
    : changeRequest

  const feature_states = await Promise.all(
    res.feature_states.map(addFeatureSegmentsToFeatureStates),
  )

  return {
    ...res,
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
        return Promise.all([
          data.get(
            `${Project.api}environments/${environmentId}/featurestates/?feature=${res.feature_states[0].feature}`,
          ),
          data.get(
            `${Project.api}projects/${projectId}/features/${res.feature_states[0].feature}/`,
          ),
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
  getChangeRequests: (envId, { committed, live_from_after }, page) => {
    const has4EyesPermission =
      Utils.getPlansPermission('4_EYES') ||
      Utils.getPlansPermission('SCHEDULE_FLAGS')
    if (!has4EyesPermission) {
      return
    }

    if (!envId) {
      return
    }
    store.loading()
    store.envId = envId
    const committedParams = `${
      committed || live_from_after ? 'committed=1' : 'committed=0'
    }` // request only committed for closed and scheduled
    const liveFromParams = live_from_after
      ? `&live_from_after=${live_from_after}`
      : '' // request live from after for scheduled
    const liveFromBeforeParams = committed
      ? `&live_from_before=${new Date().toISOString()}`
      : '' // request live from before for closed
    let endpoint =
      page ||
      `${Project.api}environments/${envId}/list-change-requests/?${committedParams}${liveFromParams}${liveFromBeforeParams}`
    if (!endpoint.includes('page_size')) {
      endpoint += `&page_size=${PAGE_SIZE}`
    }
    data
      .get(endpoint)
      .then((res) => {
        res.currentPage = page ? parseInt(page.split('page=')[1]) : 1
        res.pageSize = PAGE_SIZE
        if (live_from_after) {
          store.scheduled[envId] = res
        } else if (committed) {
          store.committed[envId] = res
        } else {
          store.model[envId] = res
        }
        store.loaded()
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
    case Actions.GET_CHANGE_REQUESTS:
      controller.getChangeRequests(
        action.environment,
        {
          committed: action.committed,
          live_from_after: action.live_from_after,
        },
        action.page,
      )
      break
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
