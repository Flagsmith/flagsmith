import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const getSubscriptionMetadataService = service
  .enhanceEndpoints({ addTagTypes: ['GetSubscriptionMetadata'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getSubscriptionMetadata: builder.query<
        Res['getSubscriptionMetadata'],
        Req['getSubscriptionMetadata']
      >({
        providesTags: (res) => [
          { id: res?.id, type: 'GetSubscriptionMetadata' },
        ],
        query: (query: Req['getSubscriptionMetadata']) => ({
          url: `organisations/${query.id}/get-subscription-metadata/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getSubscriptionMetadata(
  store: any,
  data: Req['getSubscriptionMetadata'],
  options?: Parameters<
    typeof getSubscriptionMetadataService.endpoints.getSubscriptionMetadata.initiate
  >[1],
) {
  return store.dispatch(
    getSubscriptionMetadataService.endpoints.getSubscriptionMetadata.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetSubscriptionMetadataQuery,
  // END OF EXPORTS
} = getSubscriptionMetadataService

/* Usage examples:
const { data, isLoading } = useGetSubscriptionMetadataQuery({ id: 2 }, {}) //get hook
const [getSubscriptionMetadata, { isLoading, data, isSuccess }] = useGetSubscriptionMetadataMutation() //create hook
getSubscriptionMetadataService.endpoints.getSubscriptionMetadata.select({id: 2})(store.getState()) //access data from any function
*/
