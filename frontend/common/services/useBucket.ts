import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'

export const bucketService = service
  .enhanceEndpoints({ addTagTypes: ['Bucket', 'ProjectFlag'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createBucket: builder.mutation<Res['bucket'], Req['createBucket']>({
        invalidatesTags: [{ id: 'LIST', type: 'Bucket' }],
        query: (query: Req['createBucket']) => ({
          body: query.body,
          method: 'POST',
          url: `projects/${query.projectId}/buckets/`,
        }),
      }),

      deleteBucket: builder.mutation<void, Req['deleteBucket']>({
        invalidatesTags: [
          { id: 'LIST', type: 'Bucket' },
          { id: 'LIST', type: 'ProjectFlag' },
        ],
        query: (query: Req['deleteBucket']) => ({
          method: 'DELETE',
          url: `projects/${query.projectId}/buckets/${query.id}/`,
        }),
      }),

      getBucket: builder.query<Res['bucket'], Req['getBucket']>({
        providesTags: (res) => [{ id: res?.id, type: 'Bucket' }],
        query: (query: Req['getBucket']) => ({
          url: `projects/${query.projectId}/buckets/${query.id}/`,
        }),
      }),

      getBuckets: builder.query<Res['buckets'], Req['getBuckets']>({
        providesTags: [{ id: 'LIST', type: 'Bucket' }],
        query: (query: Req['getBuckets']) => {
          const {
            page = 1,
            page_size = 10,
            projectId,
            search,
            sort_direction,
            sort_field,
          } = query
          const params = Utils.toParam({
            page,
            page_size,
            search,
            sort_direction: sort_direction || 'ASC',
            sort_field: sort_field || 'created_date',
          })
          return {
            url: `projects/${projectId}/buckets/?${params}`,
          }
        },
      }),

      updateBucket: builder.mutation<Res['bucket'], Req['updateBucket']>({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'Bucket' },
          { id: res?.id, type: 'Bucket' },
        ],
        query: (query: Req['updateBucket']) => ({
          body: query.body,
          method: 'PUT',
          url: `projects/${query.projectId}/buckets/${query.id}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function deleteBucket(
  store: any,
  data: Req['deleteBucket'],
  options?: Parameters<typeof bucketService.endpoints.deleteBucket.initiate>[1],
) {
  store.dispatch(bucketService.endpoints.deleteBucket.initiate(data, options))
  return Promise.all(
    store.dispatch(bucketService.util.getRunningQueriesThunk()),
  )
}

export async function getBuckets(
  store: any,
  data: Req['getBuckets'],
  options?: Parameters<typeof bucketService.endpoints.getBuckets.initiate>[1],
) {
  store.dispatch(bucketService.endpoints.getBuckets.initiate(data, options))
  return Promise.all(
    store.dispatch(bucketService.util.getRunningQueriesThunk()),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateBucketMutation,
  useDeleteBucketMutation,
  useGetBucketQuery,
  useGetBucketsQuery,
  useUpdateBucketMutation,
  // END OF EXPORTS
} = bucketService

/* Usage examples:
const { data, isLoading } = useGetBucketsQuery({ projectId: 2 }, {}) //get hook
const [createBucket, { isLoading, data, isSuccess }] = useCreateBucketMutation() //create hook
bucketService.endpoints.getBuckets.select({projectId: 2})(store.getState()) //access data from any function
*/
