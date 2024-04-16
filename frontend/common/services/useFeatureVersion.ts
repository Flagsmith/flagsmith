import { FeatureState, FeatureVersion, Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import { getStore } from 'common/store'
import {
  createVersionFeatureState,
  getVersionFeatureState,
  updateVersionFeatureState,
} from './useVersionFeatureState'
import { deleteFeatureSegment } from './useFeatureSegment'
import transformCorePaging from 'common/transformCorePaging'
import Utils from 'common/utils/utils'

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
          // Step 1: Create a new feature version
          const versionRes: { data: FeatureVersion } =
            await createFeatureVersion(getStore(), {
              environmentId: query.environmentId,
              featureId: query.featureId,
            })
          // Step 2: Get the feature states for the live version
          const currentFeatureStates: { data: FeatureState[] } =
            await getVersionFeatureState(getStore(), {
              environmentId: query.environmentId,
              featureId: query.featureId,
              sha: versionRes.data.uuid,
            })
          const res = await Promise.all(
            query.featureStates.map((featureState) => {
              // Step 3: update, create or delete feature states from the new version
              const matchingVersionState = currentFeatureStates.data.find(
                (feature) => {
                  return (
                    feature.feature_segment?.segment ===
                    featureState.feature_segment?.segment
                  )
                },
              )
              // Matching feature state exists, meaning we need to either modify or delete it
              if (matchingVersionState) {
                //Feature state is marked as to remove, delete it from the current version
                if (
                  featureState.toRemove &&
                  matchingVersionState.feature_segment
                ) {
                  return deleteFeatureSegment(getStore(), {
                    id: matchingVersionState.feature_segment.id,
                  })
                }
                //Feature state is not marked as remove, so we update it
                const multivariate_feature_state_values =
                  featureState.multivariate_feature_state_values
                    ? featureState.multivariate_feature_state_values?.map(
                        (featureStateValue) => {
                          const newId =
                            matchingVersionState?.multivariate_feature_state_values?.find(
                              (v) => {
                                return (
                                  v.multivariate_feature_option ===
                                  featureStateValue.multivariate_feature_option
                                )
                              },
                            )

                          return {
                            ...featureStateValue,
                            id: newId!.id,
                          }
                        },
                      )
                    : []

                return updateVersionFeatureState(getStore(), {
                  environmentId: query.environmentId,
                  featureId: matchingVersionState.feature,
                  featureState: {
                    ...featureState,
                    feature_segment: matchingVersionState?.feature_segment
                      ? {
                          ...(matchingVersionState.feature_segment as any),
                          priority: featureState.feature_segment!.priority,
                        }
                      : undefined,
                    id: matchingVersionState.id,
                    multivariate_feature_state_values,
                    uuid: matchingVersionState.uuid,
                  },
                  id: matchingVersionState.id,
                  sha: versionRes.data.uuid,
                  uuid: matchingVersionState.uuid,
                })
              }
              // Matching feature state does not exist, meaning we need to create it
              else {
                return createVersionFeatureState(getStore(), {
                  environmentId: query.environmentId,
                  featureId: query.featureId,
                  featureState,
                  sha: versionRes.data.uuid,
                })
              }
            }),
          )
          const ret = {
            data: res.map((item) => ({
              ...item,
              version_sha: versionRes.data.uuid,
            })),
            error: res.find((v) => !!v.error)?.error,
          }
          // Step 4: Publish the feature version
          if (!query.skipPublish) {
            await publishFeatureVersion(getStore(), {
              environmentId: query.environmentId,
              featureId: query.featureId,
              sha: versionRes.data.uuid,
            })
          }

          return ret as any
        },
      }),
      createFeatureVersion: builder.mutation<
        Res['featureVersion'],
        Req['createFeatureVersion']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'FeatureVersion' }],
        query: (query: Req['createFeatureVersion']) => ({
          body: {},
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
          url: `environments/${query.environmentId}/features/${query.featureId}/versions/${query.uuid}`,
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
