import { FeatureState, FeatureVersion, Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import { getStore } from 'common/store'
import { getVersionFeatureState } from './useVersionFeatureState'
import transformCorePaging from 'common/transformCorePaging'
import Utils from 'common/utils/utils'

const transformFeatureStates = (featureStates: FeatureState[]) =>
  featureStates?.map((v) => ({
    ...v,
    feature_state_value: Utils.valueToFeatureState(v.feature_state_value),
    id: undefined,
    multivariate_feature_state_values: v.multivariate_feature_state_values?.map(
      (v) => ({
        ...v,
        id: undefined,
      }),
    ),
  }))

export const getFeatureStateCrud = (featureStates: FeatureState[]) => {
  const featureStatesToCreate: Req['createFeatureVersion']['feature_states_to_create'] =
    featureStates.filter((v) => !v.id && !v.toRemove)
  const featureStatesToUpdate: Req['createFeatureVersion']['feature_states_to_update'] =
    featureStates.filter((v) => !!v.id && !v.toRemove)
  const segment_ids_to_delete_overrides: Req['createFeatureVersion']['segment_ids_to_delete_overrides'] =
    featureStates
      .filter((v) => !!v.id && !!v.toRemove && !!v.feature_segment)
      .map((v) => v.feature_segment!.segment)

  // Step 1: Create a new feature version
  const feature_states_to_create = transformFeatureStates(featureStatesToCreate)
  const feature_states_to_update = transformFeatureStates(featureStatesToUpdate)
  return {
    feature_states_to_create,
    feature_states_to_update,
    segment_ids_to_delete_overrides,
  }
}
export const featureVersionService = service
  .enhanceEndpoints({ addTagTypes: ['FeatureVersion'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createAndSetFeatureVersion: builder.mutation<
        Res['featureVersion'],
        Req['createAndSetFeatureVersion']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'FeatureVersion' }],
        queryFn: async (query: Req['createAndSetFeatureVersion']) => {
          const {
            feature_states_to_create,
            feature_states_to_update,
            segment_ids_to_delete_overrides,
          } = getFeatureStateCrud(query.featureStates)
          const versionRes: { data: FeatureVersion } =
            await createFeatureVersion(getStore(), {
              environmentId: query.environmentId,
              featureId: query.featureId,
              feature_states_to_create,
              feature_states_to_update,
              live_from: query.liveFrom,
              publish_immediately: !query.skipPublish,
              segment_ids_to_delete_overrides,
            })

          const currentFeatureStates: { data: FeatureState[] } =
            await getVersionFeatureState(getStore(), {
              environmentId: query.environmentId,
              featureId: query.featureId,
              sha: versionRes.data.uuid,
            })

          const res = currentFeatureStates.data

          const ret = {
            error: res.find((v) => !!v.error)?.error,
            feature_states: res.map((item) => ({
              data: item,
              version_sha: versionRes.data.uuid,
            })),
            feature_states_to_create,
            feature_states_to_update,
            segment_ids_to_delete_overrides,
            version_sha: versionRes.data.uuid,
          }

          return { data: ret } as any
        },
      }),
      createFeatureVersion: builder.mutation<
        Res['featureVersion'],
        Req['createFeatureVersion']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'FeatureVersion' }],
        query: (query: Req['createFeatureVersion']) => ({
          body: query,
          method: 'POST',
          url: `environments/${query.environmentId}/features/${query.featureId}/versions/`,
        }),
      }),
      getFeatureVersion: builder.query<
        Res['featureVersion'],
        Req['getFeatureVersion']
      >({
        providesTags: (res) => [{ id: res?.uuid, type: 'FeatureVersion' }],
        query: (query: Req['getFeatureVersion']) => ({
          url: `environment-feature-versions/${query.uuid}/`,
        }),
      }),
      getFeatureVersions: builder.query<
        Res['featureVersions'],
        Req['getFeatureVersions']
      >({
        providesTags: [{ id: 'LIST', type: 'FeatureVersion' }],
        query: (query) => ({
          url: `environments/${query.environmentId}/features/${
            query.featureId
          }/versions/?${Utils.toParam(query)}`,
        }),
        transformResponse: (
          baseQueryReturnValue: Res['featureVersions'],
          meta,
          req,
        ) => {
          return transformCorePaging(req, baseQueryReturnValue)
        },
      }),
      publishFeatureVersion: builder.mutation<
        Res['featureVersion'],
        Req['publishFeatureVersion']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'FeatureVersion' }],
        query: (query: Req['publishFeatureVersion']) => ({
          body: query,
          method: 'POST',
          url: `environments/${query.environmentId}/features/${query.featureId}/versions/${query.sha}/publish/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createFeatureVersion(
  store: any,
  data: Req['createFeatureVersion'],
  options?: Parameters<
    typeof featureVersionService.endpoints.createFeatureVersion.initiate
  >[1],
) {
  return store.dispatch(
    featureVersionService.endpoints.createFeatureVersion.initiate(
      data,
      options,
    ),
  )
}
export async function publishFeatureVersion(
  store: any,
  data: Req['publishFeatureVersion'],
  options?: Parameters<
    typeof featureVersionService.endpoints.publishFeatureVersion.initiate
  >[1],
) {
  return store.dispatch(
    featureVersionService.endpoints.publishFeatureVersion.initiate(
      data,
      options,
    ),
  )
}
export async function createAndSetFeatureVersion(
  store: any,
  data: Req['createAndSetFeatureVersion'],
  options?: Parameters<
    typeof featureVersionService.endpoints.createAndSetFeatureVersion.initiate
  >[1],
) {
  return store.dispatch(
    featureVersionService.endpoints.createAndSetFeatureVersion.initiate(
      data,
      options,
    ),
  )
}
export async function getFeatureVersions(
  store: any,
  data: Req['getFeatureVersions'],
  options?: Parameters<
    typeof featureVersionService.endpoints.getFeatureVersions.initiate
  >[1],
) {
  return store.dispatch(
    featureVersionService.endpoints.getFeatureVersions.initiate(data, options),
  )
}
export async function getFeatureVersion(
  store: any,
  data: Req['getFeatureVersion'],
  options?: Parameters<
    typeof featureVersionService.endpoints.getFeatureVersion.initiate
  >[1],
) {
  return store.dispatch(
    featureVersionService.endpoints.getFeatureVersion.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateAndSetFeatureVersionMutation,
  useCreateFeatureVersionMutation,
  useGetFeatureVersionQuery,
  useGetFeatureVersionsQuery,
  // END OF EXPORTS
} = featureVersionService

/* Usage examples:
const { data, isLoading } = useGetFeatureVersionQuery({ id: 2 }, {}) //get hook
const [createFeatureVersion, { isLoading, data, isSuccess }] = useCreateFeatureVersionMutation() //create hook
featureVersionService.endpoints.getFeatureVersion.select({id: 2})(store.getState()) //access data from any function
*/
