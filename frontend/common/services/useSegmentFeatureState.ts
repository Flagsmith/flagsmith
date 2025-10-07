import { FeatureState, Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import { recursiveServiceFetch } from 'common/recursiveServiceFetch'
import Utils from 'common/utils/utils'

export const segmentFeatureStateService = service
  .enhanceEndpoints({ addTagTypes: ['SegmentFeatureState'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getSegmentFeatureStates: builder.query<
        Res['segmentFeatureStates'],
        Req['getSegmentFeatureStates']
      >({
        providesTags: (res, _, req) => [
          {
            id: `${req.segmentId}${req.environmentId}`,
            type: 'SegmentFeatureState',
          },
        ],
        queryFn: async (query, { dispatch }, _, baseQuery) => {
          try {
            const allFeatureStates = await recursiveServiceFetch<FeatureState>(
              baseQuery,
              `features/featurestates/?environment=${query.environmentId}`,
              query,
            )
            const environmentFeatureStates = allFeatureStates?.results?.filter(
              (v) => !v.identity && !v.feature_segment,
            )
            return {
              data: {
                results: environmentFeatureStates?.map((featureState) => {
                  const segmentOverride = allFeatureStates.results.find(
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

export async function getSegmentFeatureStates(
  store: any,
  data: Req['getSegmentFeatureStates'],
  options?: Parameters<
    typeof segmentFeatureStateService.endpoints.getSegmentFeatureStates.initiate
  >[1],
) {
  return store.dispatch(
    segmentFeatureStateService.endpoints.getSegmentFeatureStates.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetSegmentFeatureStatesQuery,
  // END OF EXPORTS
} = segmentFeatureStateService

/* Usage examples:
const { data, isLoading } = useGetSegmentFeatureStatesQuery({ id: 2 }, {}) //get hook
const [createSegmentFeatureStates, { isLoading, data, isSuccess }] = useCreateSegmentFeatureStatesMutation() //create hook
segmentFeatureStateService.endpoints.getSegmentFeatureStates.select({id: 2})(store.getState()) //access data from any function
*/
