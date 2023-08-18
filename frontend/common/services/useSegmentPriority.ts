import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const segmentPriorityService = service
  .enhanceEndpoints({ addTagTypes: ['SegmentPriority'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      updateSegmentPriorities: builder.mutation<
        Res['segmentPriorities'],
        Req['updateSegmentPriorities']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'SegmentPriority' }],
        query: (query: Req['updateSegmentPriorities']) => ({
          body: query,
          method: 'POST',
          url: `features/feature-segments/update-priorities/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function updateSegmentPriorities(
  store: StoreType,
  data: Req['updateSegmentPriorities'],
  options?: Parameters<
    typeof segmentPriorityService.endpoints.updateSegmentPriorities.initiate
  >[1],
) {
  return store.dispatch(
    segmentPriorityService.endpoints.updateSegmentPriorities.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useUpdateSegmentPrioritiesMutation,
  // END OF EXPORTS
} = segmentPriorityService
