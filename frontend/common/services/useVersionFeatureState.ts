import { FeatureState, FeatureVersionState, Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'

//Converts a create / update version feature state to an API payload
const convertFeatureState = (featureState: FeatureState) => {
  const res: FeatureVersionState = {
    enabled: featureState.enabled,
    feature: featureState.feature,
    feature_segment: featureState.feature_segment,
    feature_state_value: Utils.valueToFeatureState(
      featureState.feature_state_value,
    ),
    live_from: featureState.live_from,
    multivariate_feature_state_values:
      featureState.multivariate_feature_state_values?.map((v) => ({
        id: v.id,
        multivariate_feature_option: v.multivariate_feature_option,
        percentage_allocation: v.percentage_allocation,
      })),
  }
  return res
}
export const versionFeatureStateService = service
  .enhanceEndpoints({ addTagTypes: ['VersionFeatureState'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createVersionFeatureState: builder.mutation<
        Res['versionFeatureState'],
        Req['createVersionFeatureState']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'VersionFeatureState' }],
        query: (query: Req['createVersionFeatureState']) => ({
          body: convertFeatureState(query.featureState),
          method: 'POST',
          url: `environments/${query.environmentId}/features/${query.featureId}/versions/${query.sha}/featurestates/`,
        }),
      }),
      deleteVersionFeatureState: builder.mutation<
        Res['versionFeatureState'],
        Req['deleteVersionFeatureState']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'VersionFeatureState' }],
        query: (query: Req['deleteVersionFeatureState']) => ({
          body: {},
          method: 'DELETE',
          url: `environments/${query.environmentId}/features/${query.featureId}/versions/${query.sha}/featurestates/${query.id}/`,
        }),
      }),
      getVersionFeatureState: builder.query<
        Res['versionFeatureState'],
        Req['getVersionFeatureState']
      >({
        providesTags: (res, _, req) => [
          { id: req?.sha, type: 'VersionFeatureState' },
        ],
        query: (query: Req['getVersionFeatureState']) => ({
          url: `environments/${query.environmentId}/features/${query.featureId}/versions/${query.sha}/featurestates/`,
        }),
      }),
      updateVersionFeatureState: builder.mutation<
        Res['versionFeatureState'],
        Req['updateVersionFeatureState']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'VersionFeatureState' }],
        query: (query: Req['updateVersionFeatureState']) => ({
          body: {
            ...convertFeatureState(query.featureState),
            id: query.id,
            uuid: query.uuid,
          },
          method: 'PUT',
          url: `environments/${query.environmentId}/features/${query.featureId}/versions/${query.sha}/featurestates/${query.id}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createVersionFeatureState(
  store: any,
  data: Req['createVersionFeatureState'],
  options?: Parameters<
    typeof versionFeatureStateService.endpoints.createVersionFeatureState.initiate
  >[1],
) {
  return store.dispatch(
    versionFeatureStateService.endpoints.createVersionFeatureState.initiate(
      data,
      options,
    ),
  )
}
export async function updateVersionFeatureState(
  store: any,
  data: Req['updateVersionFeatureState'],
  options?: Parameters<
    typeof versionFeatureStateService.endpoints.updateVersionFeatureState.initiate
  >[1],
) {
  return store.dispatch(
    versionFeatureStateService.endpoints.updateVersionFeatureState.initiate(
      data,
      options,
    ),
  )
}
export async function deleteVersionFeatureState(
  store: any,
  data: Req['deleteVersionFeatureState'],
  options?: Parameters<
    typeof versionFeatureStateService.endpoints.deleteVersionFeatureState.initiate
  >[1],
) {
  return store.dispatch(
    versionFeatureStateService.endpoints.deleteVersionFeatureState.initiate(
      data,
      options,
    ),
  )
}
export async function getVersionFeatureState(
  store: any,
  data: Req['getVersionFeatureState'],
  options?: Parameters<
    typeof versionFeatureStateService.endpoints.getVersionFeatureState.initiate
  >[1],
) {
  return store.dispatch(
    versionFeatureStateService.endpoints.getVersionFeatureState.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateVersionFeatureStateMutation,
  useGetVersionFeatureStateQuery,
  // END OF EXPORTS
} = versionFeatureStateService

/* Usage examples:
const { data, isLoading } = useGetVersionFeatureStateQuery({ id: 2 }, {}) //get hook
const [createVersionFeatureState, { isLoading, data, isSuccess }] = useCreateVersionFeatureStateMutation() //create hook
versionFeatureStateService.endpoints.getVersionFeatureState.select({id: 2})(store.getState()) //access data from any function
*/
