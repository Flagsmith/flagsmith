import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const sendKycLinkService = service
  .enhanceEndpoints({ addTagTypes: ['SendKycLink'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createSendKycLink: builder.mutation<
        Res['sendKycLink'],
        Req['createSendKycLink']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'SendKycLink' }],
        query: (query: Req['createSendKycLink']) => ({
          body: query,
          method: 'POST',
          url: `sendKycLink`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createSendKycLink(
  store: any,
  data: Req['createSendKycLink'],
  options?: Parameters<
    typeof sendKycLinkService.endpoints.createSendKycLink.initiate
  >[1],
) {
  return store.dispatch(
    sendKycLinkService.endpoints.createSendKycLink.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateSendKycLinkMutation,
  // END OF EXPORTS
} = sendKycLinkService

/* Usage examples:
const { data, isLoading } = useGetSendKycLinkQuery({ id: 2 }, {}) //get hook
const [createSendKycLink, { isLoading, data, isSuccess }] = useCreateSendKycLinkMutation() //create hook
sendKycLinkService.endpoints.getSendKycLink.select({id: 2})(store.getState()) //access data from any function
*/
