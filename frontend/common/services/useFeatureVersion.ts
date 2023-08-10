import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const featureVersionService = service
  .enhanceEndpoints({ addTagTypes: ['FeatureVersion'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createAndPublishFeatureVersion: builder.mutation<
        Res['featureVersion'],
        Req['createAndPublishFeatureVersion']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'FeatureVersion' }],
        query: (query: Req['createFeatureVersion']) => ({
          body: query,
          method: 'POST',
          url: `environments/${query.id}/features/:id2/versions/`,
        }),
      }),
      createFeatureVersion: builder.mutation<
        Res['featureVersion'],
        Req['createFeatureVersion']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'FeatureVersion' }],
        query: (query: Req['createFeatureVersion']) => ({
          body: query,
          method: 'POST',
          url: `environments/${query.id}/features/:id2/versions/`,
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
// END OF FUNCTION_EXPORTS

export const {
  useCreateFeatureVersionMutation,
  // END OF EXPORTS
} = featureVersionService

/* Usage examples:
const { data, isLoading } = useGetFeatureVersionQuery({ id: 2 }, {}) //get hook
const [createFeatureVersion, { isLoading, data, isSuccess }] = useCreateFeatureVersionMutation() //create hook
featureVersionService.endpoints.getFeatureVersion.select({id: 2})(store.getState()) //access data from any function
*/
