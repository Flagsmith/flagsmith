import { FeatureState, PagedResponse, Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'
import { getFeatureSegment } from './useFeatureSegment'
import { getStore } from 'common/store'
const _data = require('../data/base/_data')
export const addFeatureSegmentsToFeatureStates = async (v) => {
  if (!v.feature_segment) {
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
// END OF FUNCTION_EXPORTS

export const {
  useGetFeatureStatesQuery,
  // END OF EXPORTS
} = featureStateService

/* Usage examples:
const { data, isLoading } = useGetFeatureStatesQuery({ id: 2 }, {}) //get hook
const [createFeatureStates, { isLoading, data, isSuccess }] = useCreateFeatureStatesMutation() //create hook
featureStateService.endpoints.getFeatureStates.select({id: 2})(store.getState()) //access data from any function
*/
