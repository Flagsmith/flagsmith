import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const featureSegmentService = service
  .enhanceEndpoints({ addTagTypes: ['FeatureSegment'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      deleteFeatureSegment: builder.mutation<
        Res['featureSegment'],
        Req['deleteFeatureSegment']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'FeatureSegment' }],
        query: (query: Req['deleteFeatureSegment']) => ({
          body: query,
          method: 'DELETE',
          url: `features/feature-segments/${query.id}/`,
        }),
      }),
      getFeatureSegment: builder.query<
        Res['featureSegment'],
        Req['getFeatureSegment']
      >({
        providesTags: (res) => [{ id: res?.id, type: 'FeatureSegment' }],
        query: (query: Req['getFeatureSegment']) => ({
          url: `features/feature-segments/${query.id}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function deleteFeatureSegment(
  store: any,
  data: Req['deleteFeatureSegment'],
  options?: Parameters<
    typeof featureSegmentService.endpoints.deleteFeatureSegment.initiate
  >[1],
) {
  return store.dispatch(
    featureSegmentService.endpoints.deleteFeatureSegment.initiate(
      data,
      options,
    ),
  )
}
export async function getFeatureSegment(
  store: any,
  data: Req['getFeatureSegment'],
  options?: Parameters<
    typeof featureSegmentService.endpoints.getFeatureSegment.initiate
  >[1],
) {
  return store.dispatch(
    featureSegmentService.endpoints.getFeatureSegment.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useDeleteFeatureSegmentMutation,
  useGetFeatureSegmentQuery,
  // END OF EXPORTS
} = featureSegmentService

/* Usage examples:
const { data, isLoading } = useGetFeatureSegmentQuery({ id: 2 }, {}) //get hook
const [createFeatureSegment, { isLoading, data, isSuccess }] = useCreateFeatureSegmentMutation() //create hook
featureSegmentService.endpoints.getFeatureSegment.select({id: 2})(store.getState()) //access data from any function
*/
