import { ChangeSet, FeatureState, Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'

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
    feature_states_to_create: [],
    feature_states_to_update: [],
    segment_ids_to_delete_overrides: [],
  }
  try {
    parsedChangeSet.feature_states_to_create = JSON.parse(
      changeSet.feature_states_to_create,
    )
  } catch (e) {}
  try {
    parsedChangeSet.feature_states_to_update = JSON.parse(
      changeSet.feature_states_to_update,
    )
  } catch (e) {}
  try {
    parsedChangeSet.segment_ids_to_delete_overrides = JSON.parse(
      changeSet.segment_ids_to_delete_overrides,
    )
  } catch (e) {}

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
) {
  let mergedFeatureStates = (featureStates || []).concat([])

  const safeChangeSets = changeSets || []
  safeChangeSets.forEach((changeSet) => {
    const parsedChangeSet = parseChangeSet(changeSet)
    const toUpsert = (parsedChangeSet.feature_states_to_create || []).concat(
      parsedChangeSet.feature_states_to_update,
    )
    toUpsert.forEach((v) => {
      /*if there's an existing feature state, replace it
      otherwise, add to the list of feature states*/
      mergedFeatureStates = mergedFeatureStates
        .filter((changeSetFeatureState) => {
          return !featureStates?.find(
            (featureState) =>
              changeSetFeatureState.feature_segment?.segment ===
              featureState.feature_segment?.segment,
          )
        })
        .concat([v])
    }, [])
    //Remove any to delete segment overrides
    mergedFeatureStates = mergedFeatureStates.filter(
      (v) =>
        !!v.feature_segment?.segment &&
        parsedChangeSet.segment_ids_to_delete_overrides?.includes(
          v.feature_segment?.segment,
        ),
    )
  })
  return mergedFeatureStates
}
