import Constants from 'common/constants'
import { getIsWidget } from 'components/pages/WidgetPage'
import ProjectStore from './project-store'
import { createAndSetFeatureVersion } from 'common/services/useFeatureVersion'
import { updateSegmentPriorities } from 'common/services/useSegmentPriority'
import {
  createProjectFlag,
  updateProjectFlag,
} from 'common/services/useProjectFlag'
import OrganisationStore from './organisation-store'
import {
  Approval,
  Environment,
  FeatureState,
  MultivariateOption,
  ProjectFlag,
} from 'common/types/responses'
import Utils from 'common/utils/utils'
import Actions from 'common/dispatcher/action-constants'
import Project from 'common/project'
const Dispatcher = require('common/dispatcher/dispatcher')
const BaseStore = require('./base/_store')
const data = require('../data/base/_data')
const { createSegmentOverride } = require('../services/useSegmentOverride')
const { getStore } = require('../store')
import flagsmith from 'flagsmith'
import API from 'project/api'
import segmentOverrides from 'components/SegmentOverrides'
import { Req } from 'common/types/requests'
let createdFirstFeature = false
const PAGE_SIZE = 200
function recursivePageGet(url, parentRes) {
  return data.get(url).then((res) => {
    let response
    if (parentRes) {
      response = {
        ...parentRes,
        results: parentRes.results.concat(res.results),
      }
    } else {
      response = res
    }
    if (res.next) {
      return recursivePageGet(res.next, response)
    }
    return Promise.resolve(response)
  })
}

const convertSegmentOverrideToFeatureState = (
  override,
  i,
  changeRequest?: Req['createChangeRequest'],
) => {
  return {
    enabled: override.enabled,
    feature_segment: {
      id: override.id,
      priority: i,
      segment: override.segment,
      uuid: override.uuid,
    },
    feature_state_value: override.value,
    id: override.id,
    live_from: changeRequest?.live_from,
    toRemove: override.toRemove,
  } as Partial<FeatureState>
}
const controller = {
  createFlag(projectId, environmentId, flag) {
    store.saving()
    API.trackEvent(Constants.events.CREATE_FEATURE)
    if (
      !createdFirstFeature &&
      !flagsmith.getTrait('first_feature') &&
      AccountStore.model.organisations.length === 1 &&
      OrganisationStore.model.projects.length === 1 &&
      (!store.model.features || !store.model.features.length)
    ) {
      createdFirstFeature = true
      flagsmith.setTrait('first_feature', 'true')
      API.trackEvent(Constants.events.CREATE_FIRST_FEATURE)
      window.lintrk?.('track', { conversion_id: 16798354 })
    }

    createProjectFlag(getStore(), {
      body: Object.assign({}, flag, {
        initial_value:
          typeof flag.initial_value !== 'undefined' &&
          flag.initial_value !== null
            ? `${flag.initial_value}`
            : flag.initial_value,
        multivariate_options: undefined,
        project: projectId,
        type:
          flag.multivariate_options && flag.multivariate_options.length
            ? 'MULTIVARIATE'
            : 'STANDARD',
      }),
      project_id: projectId,
    })
      .then((res) =>
        Promise.all(
          (flag.multivariate_options || []).map((v) =>
            data
              .post(
                `${Project.api}projects/${projectId}/features/${res.data.id}/mv-options/`,
                {
                  ...v,
                  feature: res.data.id,
                },
              )
              .then(() => res.data),
          ),
        ).then(() =>
          data.get(
            `${Project.api}projects/${projectId}/features/${res.data.id}/`,
          ),
        ),
      )
      .then(() =>
        Promise.all([
          data.get(`${Project.api}projects/${projectId}/features/`),
          data.get(
            `${Project.api}environments/${environmentId}/featurestates/`,
          ),
        ]).then(([features, environmentFeatures]) => {
          store.model = {
            features: features.results,
            keyedEnvironmentFeatures:
              environmentFeatures &&
              _.keyBy(environmentFeatures.results, 'feature'),
          }
          store.model.lastSaved = new Date().valueOf()
          store.saved({ createdFlag: flag.name })
        }),
      )
      .catch((e) => API.ajaxHandler(store, e))
  },
  editFeature(projectId, flag, onComplete) {
    if (flag.skipSaveProjectFeature) {
      // users without CREATE_FEATURE permissions automatically hit this action, if that's the case we skip the following API calls
      onComplete({
        ...flag,
        skipSaveProjectFeature: undefined,
      })
      return
    }
    updateProjectFlag(getStore(), {
      body: flag,
      feature_id: flag.id,
      project_id: projectId,
    })
      .then((res) => {
        // onComplete calls back preserving the order of multivariate_options with their updated ids
        if (onComplete) {
          onComplete(res)
        }
        if (store.model) {
          const index = _.findIndex(store.model.features, { id: flag.id })
          store.model.features[index] = controller.parseFlag(flag)
          store.model.lastSaved = new Date().valueOf()
          store.changed()
        }
      })
      .catch((e) => {
        // onComplete calls back preserving the order of multivariate_options with their updated ids
        if (onComplete) {
          onComplete(flag)
        } else {
          API.ajaxHandler(store, e)
        }
      })
  },
  editFeatureMv(projectId, flag, onComplete) {
    if (flag.skipSaveProjectFeature) {
      // users without CREATE_FEATURE permissions automatically hit this action, if that's the case we skip the following API calls
      onComplete({
        ...flag,
        skipSaveProjectFeature: undefined,
      })
      return
    }
    const originalFlag =
      store.model && store.model.features
        ? store.model.features.find((v) => v.id === flag.id)
        : flag

    Promise.all(
      (flag.multivariate_options || []).map((v, i) => {
        const originalMV = v.id
          ? originalFlag.multivariate_options.find((m) => m.id === v.id)
          : null
        const url = `${Project.api}projects/${projectId}/features/${flag.id}/mv-options/`
        const mvData = {
          ...v,
          default_percentage_allocation: 0,
          feature: flag.id,
        }
        return (
          originalMV
            ? data.put(`${url}${originalMV.id}/`, mvData)
            : data.post(url, mvData)
        ).then((res) => {
          // It's important to preserve the original order of multivariate_options, so that editing feature states can use the updated ID
          flag.multivariate_options[i] = res
          return {
            ...v,
            id: res.id,
          }
        })
      }),
    )
      .then(() => {
        const deletedMv = originalFlag.multivariate_options.filter(
          (v) => !flag.multivariate_options.find((x) => v.id === x.id),
        )
        return Promise.all(
          deletedMv.map((v) =>
            data.delete(
              `${Project.api}projects/${projectId}/features/${flag.id}/mv-options/${v.id}/`,
            ),
          ),
        )
      })
      .then(() => {
        if (onComplete) {
          onComplete(flag)
        }
      })
  },
  editFeatureState: (
    projectId,
    environmentId,
    flag,
    projectFlag,
    environmentFlag,
    segmentOverrides,
    mode,
    onComplete,
  ) => {
    let prom
    store.saving()
    API.trackEvent(Constants.events.EDIT_FEATURE)
    const env = ProjectStore.getEnvironment(environmentId)
    if (env.use_v2_feature_versioning) {
      controller.editVersionedFeatureState(
        projectId,
        environmentId,
        flag,
        projectFlag,
        environmentFlag,
        segmentOverrides,
        mode,
        onComplete,
      )
      return
    }
    const segmentOverridesProm = (segmentOverrides || [])
      .map((v, i) => () => {
        if (v.toRemove) {
          return (
            v.id
              ? data.delete(`${Project.api}features/feature-segments/${v.id}/`)
              : Promise.resolve()
          ).then(() => {
            segmentOverrides = segmentOverrides.filter((s) => v.id !== s.id)
          })
        }
        if (!v.id) {
          const featureFlagId = v.feature
          return createSegmentOverride(
            getStore(),
            {
              enabled: !!v.enabled,
              environmentId,
              featureId: featureFlagId,
              feature_segment: {
                segment: v.segment,
              },
              feature_state_value: {
                boolean_value:
                  v.feature_segment_value.feature_state_value.boolean_value,
                integer_value:
                  v.feature_segment_value.feature_state_value.integer_value,
                string_value:
                  v.feature_segment_value.feature_state_value.string_value,
                type: v.feature_segment_value.feature_state_value.type,
              },
            },
            { forceRefetch: true },
          ).then((segmentOverride) => {
            const newValue = {
              environment: segmentOverride.data.environment,
              feature: featureFlagId,
              feature_segment_value: {
                change_request: segmentOverride.data.change_request,
                created_at: segmentOverride.data.created_at,
                deleted_at: segmentOverride.data.deleted_at,
                enabled: segmentOverride.data.enabled,
                environment: segmentOverride.data.environment,
                feature: featureFlagId,
                feature_state_value: segmentOverride.data.feature_state_value,
                id: segmentOverride.data.id,
                identity: segmentOverride.data.identity,
                live_from: segmentOverride.data.live_from,
                updated_at: segmentOverride.data.updated_at,
                uuid: segmentOverride.data.uuid,
              },
              id: segmentOverride.data.feature_segment.id,
              multivariate_options: segmentOverrides[i].multivariate_options,
              priority: segmentOverride.data.feature_segment.priority,
              segment: segmentOverride.data.feature_segment.segment,
              segment_name: v.segment_name,
              uuid: segmentOverride.data.feature_segment.uuid,
              value: segmentOverrides[i].value,
            }
            segmentOverrides[i] = newValue
          })
        }
        return Promise.resolve()
      })
      .reduce(
        (promise, currPromise) => promise.then((val) => currPromise(val)),
        Promise.resolve(),
      )

    store.saving()
    API.trackEvent(Constants.events.EDIT_FEATURE)
    segmentOverridesProm.then(() => {
      if (mode !== 'VALUE') {
        prom = Promise.resolve()
      } else if (environmentFlag) {
        prom = data
          .get(
            `${Project.api}environments/${environmentId}/featurestates/${environmentFlag.id}/`,
          )
          .then((environmentFeatureStates) => {
            const multivariate_feature_state_values =
              environmentFeatureStates.multivariate_feature_state_values &&
              environmentFeatureStates.multivariate_feature_state_values.map(
                (v) => {
                  const matching =
                    environmentFlag.multivariate_feature_state_values.find(
                      (m) => m.id === v.multivariate_feature_option,
                    ) || {}
                  return {
                    ...v,
                    percentage_allocation:
                      matching.default_percentage_allocation,
                  }
                },
              )
            environmentFlag.multivariate_feature_state_values =
              multivariate_feature_state_values
            return data.put(
              `${Project.api}environments/${environmentId}/featurestates/${environmentFlag.id}/`,
              Object.assign({}, environmentFlag, {
                enabled: flag.default_enabled,
                feature_state_value: flag.initial_value,
              }),
            )
          })
      } else {
        prom = data.post(
          `${Project.api}environments/${environmentId}/featurestates/`,
          Object.assign({}, flag, {
            enabled: false,
            environment: environmentId,
            feature: projectFlag,
          }),
        )
      }

      const segmentOverridesRequest =
        mode === 'SEGMENT' && segmentOverrides
          ? (segmentOverrides.length
              ? updateSegmentPriorities(
                  getStore(),
                  segmentOverrides.map((override, index) => ({
                    id: override.id,
                    priority: index,
                  })),
                )
              : Promise.resolve([])
            ).then(() =>
              Promise.all(
                segmentOverrides.map((override) =>
                  data.put(
                    `${Project.api}features/featurestates/${override.feature_segment_value.id}/`,
                    {
                      ...override.feature_segment_value,
                      enabled: override.enabled,
                      feature_state_value: Utils.valueToFeatureState(
                        override.value,
                      ),
                      multivariate_feature_state_values:
                        override.multivariate_options &&
                        override.multivariate_options.map((o) => {
                          if (o.multivariate_feature_option) return o
                          return {
                            multivariate_feature_option:
                              environmentFlag.multivariate_feature_state_values[
                                o.multivariate_feature_option_index
                              ].multivariate_feature_option,
                            percentage_allocation: o.percentage_allocation,
                          }
                        }),
                    },
                  ),
                ),
              ),
            )
          : Promise.resolve()

      Promise.all([prom, segmentOverridesRequest]).then(([res, segmentRes]) => {
        if (store.model) {
          store.model.keyedEnvironmentFeatures[projectFlag.id] = res
          if (segmentRes) {
            const feature = _.find(
              store.model.features,
              (f) => f.id === projectFlag.id,
            )
            if (feature) {
              feature.feature_segments = _.map(
                segmentRes.feature_segments,
                (segment) => ({
                  ...segment,
                  segment: segment.segment.id,
                }),
              )
            }
          }
        }

        if (store.model) {
          store.model.lastSaved = new Date().valueOf()
        }
        onComplete && onComplete()
        store.saved({})
      })
    })
  },
  editFeatureStateChangeRequest: async (
    projectId: string,
    environmentId: string,
    flag: ProjectFlag,
    projectFlag: ProjectFlag,
    environmentFlag: FeatureState,
    segmentOverrides: any,
    changeRequest: Req['createChangeRequest'],
    commit: boolean,
    mode: 'VALUE' | 'SEGMENT',
  ) => {
    store.saving()
    API.trackEvent(Constants.events.EDIT_FEATURE)
    const env: Environment = ProjectStore.getEnvironment(environmentId) as any
    let environment_feature_versions = []
    if (env.use_v2_feature_versioning) {
      let featureStates
      if (mode === 'SEGMENT') {
        featureStates = segmentOverrides?.map((override: any, i: number) =>
          convertSegmentOverrideToFeatureState(override, i, changeRequest),
        )
      } else {
        featureStates = [
          Object.assign({}, environmentFlag, {
            enabled: flag.default_enabled,
            feature_state_value: flag.initial_value,
            live_from: flag.live_from,
          }),
        ]
      }

      const version = await createAndSetFeatureVersion(getStore(), {
        environmentId: env.id,
        featureId: projectFlag.id,
        featureStates,
        skipPublish: true,
      })
      environment_feature_versions = version.data.map((v) => v.version_sha)
    }
    const prom = data
      .get(
        `${Project.api}environments/${environmentId}/featurestates/${environmentFlag.id}/`,
      )
      .then(() => {
        const {
          approvals,
          featureStateId,
          multivariate_options,
          ...changeRequestData
        } = changeRequest

        const userApprovals = approvals.filter((u) => {
          const keys = Object.keys(u)
          return keys.includes('user')
        })

        const group_assignments = approvals.filter((g) => {
          const keys = Object.keys(g)
          return keys.includes('group')
        })

        const req = {
          approvals: userApprovals,
          environment_feature_versions,
          feature_states: !env.use_v2_feature_versioning
            ? [
                {
                  enabled: flag.default_enabled,
                  feature: projectFlag.id,
                  feature_state_value: Utils.valueToFeatureState(
                    flag.initial_value,
                  ),
                  id: featureStateId,
                  live_from:
                    changeRequest.live_from || new Date().toISOString(),
                },
              ]
            : [],
          group_assignments,
          ...changeRequestData,
        }
        const reqType = req.id ? 'put' : 'post'
        const url = req.id
          ? `${Project.api}features/workflows/change-requests/${req.id}/`
          : `${Project.api}environments/${environmentId}/create-change-request/`
        return data[reqType](url, req).then((v) => {
          let prom = Promise.resolve()
          if (multivariate_options && v.feature_states?.[0]) {
            v.feature_states[0].multivariate_feature_state_values =
              v.feature_states[0].multivariate_feature_state_values.map((v) => {
                const matching = multivariate_options.find(
                  (m) =>
                    (v.multivariate_feature_option || v.id) ===
                    (m.multivariate_feature_option || m.id),
                )
                return {
                  ...v,
                  percentage_allocation: matching
                    ? typeof matching.percentage_allocation === 'number'
                      ? matching.percentage_allocation
                      : matching.default_percentage_allocation
                    : v.percentage_allocation,
                }
              })
          }

          prom = data
            .put(`${Project.api}features/workflows/change-requests/${v.id}/`, {
              ...v,
            })
            .then((v) => {
              if (commit) {
                AppActions.actionChangeRequest(v.id, 'commit', () => {
                  AppActions.refreshFeatures(projectId, environmentId)
                })
              } else {
                AppActions.getChangeRequest(v.id, projectId, environmentId)
              }
            })
          prom.then(() => {
            AppActions.getChangeRequests(environmentId, {})
            AppActions.getChangeRequests(environmentId, { committed: true })
            AppActions.getChangeRequests(environmentId, {
              live_from_after: new Date().toISOString(),
            })

            if (featureStateId) {
              AppActions.getChangeRequest(
                changeRequestData.id,
                projectId,
                environmentId,
              )
            }
          })
        })
      })

    Promise.all([prom]).then(() => {
      store.saved({ changeRequest: true, isCreate: true })
    })
  },
  editVersionedFeatureState: (
    projectId,
    environmentId,
    flag,
    projectFlag,
    environmentFlag,
    segmentOverrides,
    mode,
    onComplete,
  ) => {
    let prom

    if (mode !== 'VALUE') {
      // Create a new version with segment overrides
      const featureStates = segmentOverrides?.map(
        convertSegmentOverrideToFeatureState,
      )
      prom = ProjectStore.getEnvironmentIdFromKeyAsync(
        projectId,
        environmentId,
      ).then((res) => {
        return createAndSetFeatureVersion(getStore(), {
          environmentId: res,
          featureId: projectFlag.id,
          featureStates,
        }).then((res) => {
          if (res.error) {
            throw res.error
          }
        })
      })
    } else if (environmentFlag) {
      // Create a new version with feature state / multivariate options
      prom = data
        .get(
          `${Project.api}environments/${environmentId}/featurestates/${environmentFlag.id}/`,
        )
        .then((environmentFeatureStates) => {
          // Match all multivariate options to stored ids
          const multivariate_feature_state_values =
            environmentFeatureStates.multivariate_feature_state_values &&
            environmentFeatureStates.multivariate_feature_state_values.map(
              (v) => {
                const matching =
                  environmentFlag.multivariate_feature_state_values.find(
                    (m) => m.id === v.multivariate_feature_option,
                  ) || {}
                return {
                  ...v,
                  percentage_allocation: matching.default_percentage_allocation,
                }
              },
            )
          environmentFlag.multivariate_feature_state_values =
            multivariate_feature_state_values

          return ProjectStore.getEnvironmentIdFromKeyAsync(
            projectId,
            environmentId,
          ).then((res) => {
            const data = Object.assign({}, environmentFlag, {
              enabled: flag.default_enabled,
              feature_state_value: flag.initial_value,
            })
            return createAndSetFeatureVersion(getStore(), {
              environmentId: res,
              featureId: projectFlag.id,
              featureStates: [data],
            }).then((res) => {
              if (res.error) {
                throw res.error
              }
              const featureState = res.data[0].data
              store.model.keyedEnvironmentFeatures[projectFlag.id] = {
                ...featureState,
                feature_state_value: Utils.featureStateToValue(
                  featureState.feature_state_value,
                ),
              }
            })
          })
        })
    } else {
      prom = data.post(
        `${Project.api}environments/${environmentId}/featurestates/`,
        Object.assign({}, flag, {
          enabled: false,
          environment: environmentId,
          feature: projectFlag,
        }),
      )
    }

    prom.then((res) => {
      if (store.model) {
        store.model.lastSaved = new Date().valueOf()
      }
      onComplete && onComplete()
      store.saved({})
    })
  },
  getFeatureUsage(projectId, environmentId, flag, period) {
    data
      .get(
        `${Project.api}projects/${projectId}/features/${flag}/evaluation-data/?period=${period}&environment_id=${environmentId}`,
      )
      .then((result) => {
        const firstResult = result[0]
        const lastResult = firstResult && result[result.length - 1]
        const diff = firstResult
          ? moment(lastResult.day, 'YYYY-MM-DD').diff(
              moment(firstResult.day, 'YYYY-MM-DD'),
              'days',
            )
          : 0
        if (firstResult && diff) {
          _.range(0, diff).map((v) => {
            const day = moment(firstResult.day)
              .add(v, 'days')
              .format('YYYY-MM-DD')
            if (!result.find((v) => v.day === day)) {
              result.push({
                'count': 0,
                day,
              })
            }
          })
        }
        store.model.usageData = _.sortBy(result, (v) =>
          moment(v.day, 'YYYY-MM-DD').valueOf(),
        ).map((v) => ({
          ...v,
          day: moment(v.day, 'YYYY-MM-DD').format('Do MMM'),
        }))
        store.changed()
      })
  },
  getFeatures: (projectId, environmentId, force, page, filter, pageSize) => {
    if (!store.model || store.envId !== environmentId || force) {
      store.envId = environmentId
      store.projectId = projectId
      store.environmentId = environmentId
      store.page = page
      store.filter = filter
      let filterUrl = ''
      const { feature } = Utils.fromParam()
      if (Object.keys(store.filter).length) {
        filterUrl = `&${Utils.toParam(store.filter)}`
      }

      ProjectStore.getEnvironmentIdFromKeyAsync(projectId, environmentId).then(
        (environment) => {
          let featuresEndpoint =
            typeof page === 'string'
              ? page
              : `${Project.api}projects/${projectId}/features/?page=${
                  page || 1
                }&page_size=${pageSize || PAGE_SIZE}${filterUrl}`
          if (store.search) {
            featuresEndpoint += `&search=${store.search}`
          }
          if (store.sort) {
            featuresEndpoint += `&environment=${environment}&sort_field=${
              store.sort.sortBy
            }&sort_direction=${store.sort.sortOrder.toUpperCase()}`
          }

          return Promise.all([
            data.get(featuresEndpoint),
            recursivePageGet(
              `${Project.api}environments/${environmentId}/featurestates/?page_size=${PAGE_SIZE}`,
            ),
            feature
              ? data.get(
                  `${Project.api}projects/${projectId}/features/${feature}/`,
                )
              : Promise.resolve(),
          ])
            .then(([features, environmentFeatures, feature]) => {
              if (store.filter !== filter) {
                //The filter has been changed since, ignore the api response. This will be resolved when moving to RTK.
                return
              }
              store.paging.next = features.next
              store.paging.pageSize = PAGE_SIZE
              store.paging.count = features.count
              store.paging.previous = features.previous
              store.paging.currentPage =
                featuresEndpoint.indexOf('?page=') !== -1
                  ? parseInt(
                      featuresEndpoint.substr(
                        featuresEndpoint.indexOf('?page=') + 6,
                      ),
                    )
                  : 1

              if (feature) {
                const index = features.results.findIndex(
                  (v) => v.id === feature.id,
                )
                if (index === -1) {
                  features.results.push({ ...feature, ignore: true })
                }
              }
              if (features.results.length) {
                createdFirstFeature = true
              }

              store.model = {
                features: features.results.map(controller.parseFlag),
                keyedEnvironmentFeatures:
                  environmentFeatures.results &&
                  _.keyBy(environmentFeatures.results, 'feature'),
              }
              store.loaded()
            })
            .catch((e) => {
              if (!getIsWidget()) {
                document.location.href = '/404?entity=environment'
              }
              API.ajaxHandler(store, e)
            })
        },
      )
    }
  },
  parseFlag(flag) {
    return {
      ...flag,
      feature_segments:
        flag.feature_segments &&
        flag.feature_segments.map((fs) => ({
          ...fs,
          segment: fs.segment.id,
        })),
    }
  },
  removeFlag: (projectId, flag) => {
    store.saving()
    API.trackEvent(Constants.events.REMOVE_FEATURE)
    return data
      .delete(`${Project.api}projects/${projectId}/features/${flag.id}/`)
      .then(() => {
        store.model.features = _.filter(
          store.model.features,
          (f) => f.id !== flag.id,
        )
        store.model.lastSaved = new Date().valueOf()
        store.saved({})
      })
  },
  searchFeatures: _.throttle(
    (search, environmentId, projectId, filter, pageSize) => {
      store.search = search
      controller.getFeatures(
        projectId,
        environmentId,
        true,
        0,
        filter,
        pageSize,
      )
    },
    1000,
  ),
}

const store = Object.assign({}, BaseStore, {
  getEnvironmentFlags() {
    return store.model && store.model.keyedEnvironmentFeatures
  },
  getFeatureUsage() {
    return store.model && store.model.usageData
  },
  getLastSaved() {
    return store.model && store.model.lastSaved
  },
  getProjectFlags() {
    return store.model && store.model.features
  },
  hasFlagInEnvironment(id, environmentFlags) {
    const flags =
      environmentFlags || (store.model && store.model.keyedEnvironmentFeatures)

    // eslint-disable-next-line no-prototype-builtins
    return flags && flags.hasOwnProperty(id)
  },
  id: 'features',
  paging: {},
  sort: { default: true, label: 'Name', sortBy: 'name', sortOrder: 'asc' },
})

store.dispatcherIndex = Dispatcher.register(store, (payload) => {
  const action = payload.action // this is our action from handleViewAction

  switch (action.actionType) {
    case Actions.SEARCH_FLAGS: {
      if (action.sort) {
        store.sort = action.sort
      }
      controller.searchFeatures(
        action.search,
        action.environmentId,
        action.projectId,
        action.filter,
        action.pageSize,
      )
      break
    }
    case Actions.GET_FLAGS:
      store.search = action.search || ''
      if (action.sort) {
        store.sort = action.sort
      }
      controller.getFeatures(
        action.projectId,
        action.environmentId,
        action.force,
        action.page,
        action.filter,
        action.pageSize,
      )
      break
    case Actions.REFRESH_FEATURES:
      if (
        action.projectId === store.projectId &&
        action.environmentId === store.environmentId
      ) {
        controller.getFeatures(
          store.projectId,
          store.environmentId,
          true,
          store.page,
          store.filter,
        )
      }
      break
    case Actions.GET_FEATURE_USAGE:
      controller.getFeatureUsage(
        action.projectId,
        action.environmentId,
        action.flag,
        action.period,
      )
      break
    case Actions.CREATE_FLAG:
      controller.createFlag(action.projectId, action.environmentId, action.flag)
      break
    case Actions.EDIT_ENVIRONMENT_FLAG:
      controller.editFeatureState(
        action.projectId,
        action.environmentId,
        action.flag,
        action.projectFlag,
        action.environmentFlag,
        action.segmentOverrides,
        action.mode,
        action.onComplete,
      )
      break
    case Actions.EDIT_ENVIRONMENT_FLAG_CHANGE_REQUEST:
      controller.editFeatureStateChangeRequest(
        action.projectId,
        action.environmentId,
        action.flag,
        action.projectFlag,
        action.environmentFlag,
        action.segmentOverrides,
        action.changeRequest,
        action.commit,
        action.mode,
      )
      break
    case Actions.EDIT_FEATURE:
      controller.editFeature(action.projectId, action.flag, action.onComplete)
      break
    case Actions.EDIT_FEATURE_MV:
      controller.editFeatureMv(action.projectId, action.flag, action.onComplete)
      break
    case Actions.REMOVE_FLAG:
      controller.removeFlag(action.projectId, action.flag)
      break
    default:
  }
})
controller.store = store
export default controller.store
