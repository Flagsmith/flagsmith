import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const featureService = service
  .enhanceEndpoints({ addTagTypes: ['Feature'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getFeatures: builder.query<Res['features'], Req['getFeatures']>({
        providesTags: [{ id: 'LIST', type: 'Feature' }],
        query: () => ({
          url: `features`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getFeatures(
  store: any,
  data: Req['getFeatures'],
  options?: Parameters<typeof featureService.endpoints.getFeatures.initiate>[1],
) {
  return store.dispatch(
    featureService.endpoints.getFeatures.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetFeaturesQuery,
  // END OF EXPORTS
} = featureService

/* Usage examples:
const { data, isLoading } = useGetFeaturesQuery({ id: 2 }, {}) //get hook
const [createFeatures, { isLoading, data, isSuccess }] = useCreateFeaturesMutation() //create hook
featureService.endpoints.getFeatures.select({id: 2})(store.getState()) //access data from any function
*/
