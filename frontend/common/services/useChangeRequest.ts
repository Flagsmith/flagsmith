import {
  ChangeRequest,
  ChangeSet,
  FeatureState,
  PagedResponse,
  ProjectFlag,
  Res,
} from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'
import sortBy from 'lodash/sortBy'
import moment from 'moment'
import transformCorePaging from 'common/transformCorePaging'
import { sortMultivariateOptions } from 'common/utils/multivariate'
import {
  addFeatureSegmentsToFeatureStates,
  featureStateService,
} from './useFeatureState'

export const changeRequestService = service
  .enhanceEndpoints({ addTagTypes: ['ChangeRequest'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      actionChangeRequest: builder.mutation<
        Res['actionChangeRequest'],
        Req['actionChangeRequest']
      >({
        invalidatesTags: (_, error, { id }) =>
          error
            ? []
            : [
                { id, type: 'ChangeRequest' },
                { id: 'LIST', type: 'ChangeRequest' },
              ],
        onQueryStarted: async (_, { dispatch, queryFulfilled }) => {
          try {
            await queryFulfilled
            dispatch(featureStateService.util.invalidateTags(['FeatureState']))
          } catch {
            // The mutation's own error state reports the failure
          }
        },
        query: ({ actionType, id }) => ({
          body: {},
          method: 'POST',
          url: `features/workflows/change-requests/${id}/${actionType}/`,
        }),
      }),
      createEnvironmentChangeRequest: builder.mutation<
        Res['createEnvironmentChangeRequest'],
        Req['createEnvironmentChangeRequest']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'ChangeRequest' }],
        query: ({
          approvals,
          environmentId,
          featureId,
          live_from,
          ...rest
        }) => ({
          body: {
            ...rest,
            // The modal hands back users and groups in one list.
            approvals: approvals.filter((approval) => !!approval.user),
            // The API reads the schedule from the change set, not the change
            // request, and stages dependency changes into it.
            change_sets: [
              {
                feature: featureId,
                feature_states_to_create: [],
                feature_states_to_update: [],
                live_from: live_from || new Date().toISOString(),
                segment_ids_to_delete_overrides: [],
              },
            ],
            // Required, even when empty.
            feature_states: [],
            group_assignments: approvals.filter((approval) => !!approval.group),
          },
          method: 'POST',
          url: `environments/${environmentId}/create-change-request/`,
        }),
      }),
      deleteChangeRequest: builder.mutation<void, Req['deleteChangeRequest']>({
        invalidatesTags: [{ id: 'LIST', type: 'ChangeRequest' }],
        query: ({ id }) => ({
          method: 'DELETE',
          url: `features/workflows/change-requests/${id}/`,
        }),
      }),
      getChangeRequest: builder.query<
        Res['changeRequestDetail'],
        Req['getChangeRequest']
      >({
        providesTags: (_, _2, { id }) => [{ id, type: 'ChangeRequest' }],
        queryFn: async (
          { environmentId, id, projectId },
          _api,
          _extraOptions,
          baseQuery,
        ) => {
          const res = await baseQuery({
            url: `features/workflows/change-requests/${id}/`,
          })
          if (res.error) return { error: res.error }
          const raw = res.data as ChangeRequest
          const changeRequest: ChangeRequest = {
            ...raw,
            feature_states: await Promise.all(
              raw.feature_states.map(addFeatureSegmentsToFeatureStates),
            ),
          }
          const feature =
            changeRequest.feature_states[0]?.feature ||
            changeRequest.change_sets?.[0]?.feature
          const [environmentFlags, projectFlagRes] = await Promise.all([
            baseQuery({
              url: `environments/${environmentId}/featurestates/?feature=${feature}`,
            }),
            baseQuery({ url: `projects/${projectId}/features/${feature}/` }),
          ])
          // A 404 means the feature was deleted since, which the page explains
          if (projectFlagRes.error?.status === 404) {
            return { data: { changeRequest } }
          }
          if (projectFlagRes.error) return { error: projectFlagRes.error }
          if (environmentFlags.error) return { error: environmentFlags.error }
          const projectFlag = projectFlagRes.data as ProjectFlag
          return {
            data: {
              changeRequest,
              environmentFlag: (
                environmentFlags.data as PagedResponse<FeatureState>
              ).results[0],
              projectFlag: {
                ...projectFlag,
                multivariate_options: sortMultivariateOptions(
                  projectFlag.multivariate_options,
                ),
              },
            },
          }
        },
      }),
      getChangeRequests: builder.query<
        Res['changeRequests'],
        Req['getChangeRequests']
      >({
        providesTags: [{ id: 'LIST', type: 'ChangeRequest' }],
        query: ({ environmentId, ...rest }) => ({
          url: `environments/${environmentId}/list-change-requests/?${Utils.toParam(
            { ...rest },
          )}`,
        }),
        transformResponse: (res, _, req) => transformCorePaging(req, res),
      }),
      getScheduledChangeRequests: builder.query<
        Res['changeRequests'],
        Req['getScheduledChangeRequests']
      >({
        providesTags: [{ id: 'LIST', type: 'ChangeRequest' }],
        // Read the time per request, so a refetch after a commit uses the current time
        query: ({ environmentId, ...rest }) => ({
          url: `environments/${environmentId}/list-change-requests/?${Utils.toParam(
            {
              ...rest,
              committed: true,
              live_from_after: new Date().toISOString(),
            },
          )}`,
        }),
        transformResponse: (res, _, req) => transformCorePaging(req, res),
      }),
      updateChangeRequest: builder.mutation<
        Res['updateChangeRequest'],
        Req['updateChangeRequest']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'ChangeRequest' }],
        query: (changeRequest) => ({
          body: changeRequest,
          method: 'PUT',
          url: `features/workflows/change-requests/${changeRequest.id}/`,
        }),
      }),
      updateChangeRequestAssignees: builder.mutation<
        Res['updateChangeRequest'],
        Req['updateChangeRequestAssignees']
      >({
        invalidatesTags: (_, error, { id }) =>
          error
            ? []
            : [
                { id: `${id}`, type: 'ChangeRequest' },
                { id: 'LIST', type: 'ChangeRequest' },
              ],
        // Re-read first so the PUT carries the stored change, not the page's copy
        queryFn: async (
          { approvals, group_assignments, id },
          _api,
          _extraOptions,
          baseQuery,
        ) => {
          const url = `features/workflows/change-requests/${id}/`
          const res = await baseQuery({ url })
          if (res.error) return { error: res.error }
          const current = res.data as ChangeRequest
          const put = await baseQuery({
            body: {
              ...current,
              approvals,
              environment_feature_versions:
                current.environment_feature_versions?.map((v) => v.uuid),
              group_assignments,
            },
            method: 'PUT',
            url,
          })
          if (put.error) return { error: put.error }
          return { data: put.data as Res['updateChangeRequest'] }
        },
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getChangeRequests(
  store: any,
  data: Req['getChangeRequests'],
  options?: Parameters<
    typeof changeRequestService.endpoints.getChangeRequests.initiate
  >[1],
) {
  return store.dispatch(
    changeRequestService.endpoints.getChangeRequests.initiate(data, options),
  )
}
export async function updateChangeRequest(
  store: any,
  data: Req['updateChangeRequest'],
  options?: Parameters<
    typeof changeRequestService.endpoints.updateChangeRequest.initiate
  >[1],
) {
  return store.dispatch(
    changeRequestService.endpoints.updateChangeRequest.initiate(data, options),
  )
}
export async function actionChangeRequest(
  store: any,
  data: Req['actionChangeRequest'],
  options?: Parameters<
    typeof changeRequestService.endpoints.actionChangeRequest.initiate
  >[1],
) {
  return store.dispatch(
    changeRequestService.endpoints.actionChangeRequest.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useActionChangeRequestMutation,
  useCreateEnvironmentChangeRequestMutation,
  useDeleteChangeRequestMutation,
  useGetChangeRequestQuery,
  useGetChangeRequestsQuery,
  useGetScheduledChangeRequestsQuery,
  useUpdateChangeRequestAssigneesMutation,
  useUpdateChangeRequestMutation,
  // END OF EXPORTS
} = changeRequestService

/* Usage examples:
const { data, isLoading } = useGetChangeRequestsQuery({ id: 2 }, {}) //get hook
const [createChangeRequests, { isLoading, data, isSuccess }] = useCreateChangeRequestsMutation() //create hook
changeRequestService.endpoints.getChangeRequests.select({id: 2})(store.getState()) //access data from any function
*/
export function parseChangeSet(changeSet: ChangeSet) {
  const parsedChangeSet: {
    feature_states_to_update: FeatureState[]
    feature_states_to_create: FeatureState[]
    segment_ids_to_delete_overrides: number[]
  } = {
    feature_states_to_create: changeSet.feature_states_to_create,
    feature_states_to_update: changeSet.feature_states_to_update,
    segment_ids_to_delete_overrides: changeSet.segment_ids_to_delete_overrides,
  }

  return {
    ...parsedChangeSet,
    feature_states_to_create: Array.isArray(
      parsedChangeSet.feature_states_to_create,
    )
      ? parsedChangeSet.feature_states_to_create
      : [],
    feature_states_to_update: Array.isArray(
      parsedChangeSet.feature_states_to_update,
    )
      ? parsedChangeSet.feature_states_to_update
      : [],
    segment_ids_to_delete_overrides: Array.isArray(
      parsedChangeSet.segment_ids_to_delete_overrides,
    )
      ? parsedChangeSet.segment_ids_to_delete_overrides
      : [],
  }
}

export function mergeChangeSets(
  changeSets: ChangeSet[] | undefined,
  featureStates: FeatureState[] | undefined,
  conflicts: ChangeRequest['conflicts'] | undefined,
) {
  let mergedFeatureStates = (featureStates || []).concat([])

  const safeChangeSets = changeSets || []
  safeChangeSets.forEach((changeSet) => {
    const parsedChangeSet = parseChangeSet(changeSet)
    const toUpsert = (parsedChangeSet.feature_states_to_create || []).concat(
      parsedChangeSet.feature_states_to_update,
    )

    toUpsert.forEach((v) => {
      // Remove the existing feature state if it exists
      mergedFeatureStates = mergedFeatureStates.filter((mergedFeatureState) => {
        return (
          mergedFeatureState.feature_segment?.segment !==
          v.feature_segment?.segment
        )
      })

      // Add the new or updated feature state
      mergedFeatureStates = mergedFeatureStates.concat([v])
    })

    // Remove any to delete segment overrides
    mergedFeatureStates = mergedFeatureStates.filter(
      (v) =>
        !v.feature_segment?.segment ||
        !parsedChangeSet.segment_ids_to_delete_overrides?.includes(
          v.feature_segment?.segment,
        ),
    )
  })

  return mergedFeatureStates.map((featureState) => {
    const conflict = sortBy(
      conflicts,
      //prioritise newly published conflicts as we show those when diffing change requests
      (conflict) => -moment(conflict.published_at).valueOf(),
    )?.find(
      (conflict) =>
        (conflict.segment_id || null) ===
        (featureState.feature_segment?.segment || null),
    )
    return {
      ...featureState,
      conflict: conflict,
    }
  })
}
