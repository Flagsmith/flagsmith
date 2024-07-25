import {
  ChangeRequest,
  ChangeSet,
  FeatureState,
  Res,
} from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'
import sortBy from 'lodash/sortBy'
import moment from 'moment'

export const changeRequestService = service
  .enhanceEndpoints({ addTagTypes: ['ChangeRequest'] })
  .injectEndpoints({
    endpoints: (builder) => ({
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
// END OF FUNCTION_EXPORTS

export const {
  useGetChangeRequestsQuery,
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
