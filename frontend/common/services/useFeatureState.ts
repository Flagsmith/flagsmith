import { FeatureState, PagedResponse, Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'
import { getFeatureSegment } from './useFeatureSegment'
import { getStore } from 'common/store'
import { recursiveServiceFetch } from 'common/recursiveServiceFetch'

export const addFeatureSegmentsToFeatureStates = async (v) => {
  if (typeof v.feature_segment !== 'number') {
    return v
  }
  const featureSegmentData = await getFeatureSegment(getStore(), {
    id: v.feature_segment,
  })
  return {
    ...v,
    feature_segment: featureSegmentData.data,
  }
}
export const featureStateService = service
  .enhanceEndpoints({ addTagTypes: ['FeatureState'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getFeatureStates: builder.query<
        Res['featureStates'],
        Req['getFeatureStates']
      >({
        providesTags: [{ id: 'LIST', type: 'FeatureState' }],
        queryFn: async (query, baseQueryApi, extraOptions, baseQuery) => {
          //This endpoint returns feature_segments as a number, so it fetches the feature segments and appends
          const {
            data,
          }: {
            data: PagedResponse<
              Omit<FeatureState, 'feature_segment'> & {
                feature_segment: number | null
              }
            >
          } = await baseQuery({
            url: `features/featurestates/?${Utils.toParam(query)}`,
          })
          const results = await Promise.all(
            data.results.map(addFeatureSegmentsToFeatureStates),
          )
          return {
            data: {
              ...data,
              results,
            },
          }
        },
      }),
      getSegmentFeatureStates: builder.query<
        Res['segmentFeatureStates'],
        Req['getSegmentFeatureStates']
      >({
        providesTags: (res, _, req) => [
          {
            id: `${req.segmentId}${req.environmentId}`,
            type: 'FeatureState',
          },
        ],
        queryFn: async (query, { dispatch }, _, baseQuery) => {
          try {
            const allFeatureStates = await recursiveServiceFetch<FeatureState>(
              baseQuery,
              `features/featurestates/?environment=${query.environmentId}`,
              query,
            )
            const segmentFeatureStates =
              await recursiveServiceFetch<FeatureState>(
                baseQuery,
                `features/featurestates/?environment=${query.environmentId}&segment=${query.segmentId}`,
                query,
              )
            const environmentFeatureStates = allFeatureStates?.results?.filter(
              (v) => !v.identity && !v.feature_segment,
            )
            return {
              data: {
                results: environmentFeatureStates?.map((featureState) => {
                  const segmentOverride = segmentFeatureStates.results.find(
                    (v) =>
                      v.feature === featureState.feature && !!v.feature_segment,
                  )
                  return {
                    featureState: {
                      ...featureState,
                      feature_state_value: Utils.featureStateToValue(
                        featureState.feature_state_value,
                      ),
                    } as FeatureState,
                    segmentOverride: segmentOverride
                      ? ({
                          ...segmentOverride,
                          feature_state_value: Utils.featureStateToValue(
                            segmentOverride.feature_state_value,
                          ),
                        } as FeatureState)
                      : undefined,
                  }
                }),
              } as Res['segmentFeatureStates'],
            }
          } catch (error) {
            return { error }
          }
        },
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getFeatureStates(
  store: any,
  data: Req['getFeatureStates'],
  options?: Parameters<
    typeof featureStateService.endpoints.getFeatureStates.initiate
  >[1],
) {
  return store.dispatch(
    featureStateService.endpoints.getFeatureStates.initiate(data, options),
  )
}

export async function getSegmentFeatureStates(
  store: any,
  data: Req['getSegmentFeatureStates'],
  options?: Parameters<
    typeof featureStateService.endpoints.getSegmentFeatureStates.initiate
  >[1],
) {
  return store.dispatch(
    featureStateService.endpoints.getSegmentFeatureStates.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetFeatureStatesQuery,
  useGetSegmentFeatureStatesQuery,
  // END OF EXPORTS
} = featureStateService

/* Usage examples:
const { data, isLoading } = useGetFeatureStatesQuery({ id: 2 }, {}) //get hook
const [createFeatureStates, { isLoading, data, isSuccess }] = useCreateFeatureStatesMutation() //create hook
featureStateService.endpoints.getFeatureStates.select({id: 2})(store.getState()) //access data from any function
*/
