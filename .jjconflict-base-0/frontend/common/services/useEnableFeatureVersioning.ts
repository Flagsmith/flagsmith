import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const featureVersioningService = service
  .enhanceEndpoints({ addTagTypes: ['FeatureVersioning'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      enableFeatureVersioning: builder.mutation<
        Res['enableFeatureVersioning'],
        Req['enableFeatureVersioning']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'FeatureVersioning' }],
        query: (query: Req['enableFeatureVersioning']) => ({
          body: query,
          method: 'POST',
          url: `environments/${query.environmentId}/enable-v2-versioning/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function enableFeatureVersioning(
  store: any,
  data: Req['enableFeatureVersioning'],
  options?: Parameters<
    typeof featureVersioningService.endpoints.enableFeatureVersioning.initiate
  >[1],
) {
  return store.dispatch(
    featureVersioningService.endpoints.enableFeatureVersioning.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useEnableFeatureVersioningMutation,
  // END OF EXPORTS
} = featureVersioningService

/* Usage examples:
const { data, isLoading } = useGetFeatureVersioningQuery({ id: 2 }, {}) //get hook
const [enableFeatureVersioning, { isLoading, data, isSuccess }] = useEnableFeatureVersioningMutation() //create hook
featureVersioningService.endpoints.getFeatureVersioning.select({id: 2})(store.getState()) //access data from any function
*/
