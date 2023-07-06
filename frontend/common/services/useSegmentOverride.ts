import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const segmentOverrideService = service
  .enhanceEndpoints({ addTagTypes: ['SegmentOverride'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createSegmentOverride: builder.mutation<
        Res['createSegmentOverride'],
        Req['createSegmentOverride']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'CreateSegmentOverride' }],
        query: (query: Req['createSegmentOverride']) => ({
          body: query,
          method: 'POST',
          url: `environments/${query.environmentId}/features/${query.featureId}/create-segment-override/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createSegmentOverride(
  store: any,
  data: Req['createSegmentOverride'],
  options?: Parameters<
    typeof segmentOverrideService.endpoints.createSegmentOverride.initiate
  >[1],
) {
  return store.dispatch(
    segmentOverrideService.endpoints.createSegmentOverride.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateSegmentOverrideMutation,
  // END OF EXPORTS
} = segmentOverrideService

/* Usage examples:
const { data, isLoading } = useGetCreateSegmentOverrideQuery({ id: 2 }, {}) //get hook
const [createSegmentOverride, { isLoading, data, isSuccess }] = useCreateSegmentOverrideMutation() //create hook
segmentOverrideService.endpoints.getCreateSegmentOverride.select({id: 2})(store.getState()) //access data from any function
*/
